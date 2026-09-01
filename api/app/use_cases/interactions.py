from dataclasses import dataclass

from app.domain.detections import (
    CanonicalDetection,
    DetectionSource,
    MappingGap,
    Provenance,
)
from app.engines.deidentification import AppliedOperation, DeidentificationEngine
from app.engines.fusion import DetectionFusion
from app.engines.gazetteers import GazetteerMatcher
from app.engines.patterns import PatternRecognizerEngine
from app.engines.protection import ProtectionRuleEvaluator
from app.errors import InvalidConfigurationError
from app.repositories.configuration import ConfigurationRepository
from app.services.inference import InferenceService


@dataclass(frozen=True)
class ProtectInteractionResult:
    original_text: str
    protected_text: str
    detections: tuple[CanonicalDetection, ...]
    operations: tuple[AppliedOperation, ...]
    mapping_gaps: tuple[MappingGap, ...]
    warnings: tuple[str, ...]


class ProtectInteractionUseCase:
    def __init__(
        self,
        repository: ConfigurationRepository,
        inference: InferenceService,
        pattern_engine: PatternRecognizerEngine | None = None,
        gazetteer_matcher: GazetteerMatcher | None = None,
        fusion: DetectionFusion | None = None,
        rule_evaluator: ProtectionRuleEvaluator | None = None,
        deidentification: DeidentificationEngine | None = None,
    ):
        self._repository = repository
        self._inference = inference
        self._patterns = pattern_engine or PatternRecognizerEngine()
        self._gazetteers = gazetteer_matcher or GazetteerMatcher()
        self._fusion = fusion or DetectionFusion()
        self._rules = rule_evaluator or ProtectionRuleEvaluator()
        self._deidentification = deidentification or DeidentificationEngine()

    async def execute(self, text: str) -> ProtectInteractionResult:
        settings = await self._repository.get_detection_settings()
        canonical: list[CanonicalDetection] = []
        gaps: list[MappingGap] = []
        gap_keys: set[tuple[int, int, str]] = set()

        if settings.model_enabled:
            active_model_id = await self._repository.get_active_model_id()
            if not active_model_id:
                raise InvalidConfigurationError("No active ML model is configured.")
            result = await self._inference.detect(active_model_id, text)
            mappings = {
                mapping.native_entity_type: mapping.canonical_type
                for mapping in await self._repository.list_mappings(active_model_id)
            }
            model_detections: list[CanonicalDetection] = []
            for native in result.detections:
                if native.start < 0 or native.end > len(text) or native.end <= native.start:
                    continue
                start, end = self._expand_word_boundaries(text, native.start, native.end)
                while start < end and text[start].isspace():
                    start += 1
                while end > start and text[end - 1].isspace():
                    end -= 1
                detected_text = text[start:end]
                if not detected_text.strip():
                    continue
                canonical_type = mappings.get(native.native_type)
                if canonical_type is None:
                    gap_key = (start, end, native.native_type)
                    if gap_key in gap_keys:
                        continue
                    gap_keys.add(gap_key)
                    gaps.append(
                        MappingGap(
                            text=detected_text,
                            start=start,
                            end=end,
                            confidence=native.confidence,
                            model_id=result.model_id,
                            model_version=result.model_version,
                            native_entity_type=native.native_type,
                        )
                    )
                    continue
                model_detections.append(
                    CanonicalDetection(
                        canonical_type=canonical_type,
                        text=detected_text,
                        start=start,
                        end=end,
                        confidence=native.confidence,
                        provenance=Provenance(
                            source=DetectionSource.MODEL,
                            source_id=result.model_id,
                            model_id=result.model_id,
                            model_version=result.model_version,
                            native_entity_type=native.native_type,
                        ),
                    )
                )
            canonical.extend(self._merge_adjacent_model_detections(text, model_detections))

        if settings.pattern_enabled:
            canonical.extend(
                self._patterns.detect(text, await self._repository.list_patterns())
            )
        if settings.gazetteer_enabled:
            canonical.extend(
                self._gazetteers.detect(text, await self._repository.list_gazetteers())
            )

        final_detections = self._fusion.fuse(canonical, settings)
        decisions = self._rules.evaluate(
            final_detections,
            await self._repository.list_protection_rules(),
        )
        transformed = self._deidentification.apply(
            text,
            decisions,
            [(gap.start, gap.end, gap.text) for gap in gaps],
        )
        warnings = (
            (
                f"{len(gaps)} model detection(s) had no canonical mapping; "
                "their sensitive spans were protected conservatively.",
            )
            if gaps
            else ()
        )
        return ProtectInteractionResult(
            original_text=text,
            protected_text=transformed.protected_text,
            detections=tuple(final_detections),
            operations=transformed.operations,
            mapping_gaps=tuple(gaps),
            warnings=warnings,
        )

    @staticmethod
    def _expand_word_boundaries(text: str, start: int, end: int) -> tuple[int, int]:
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] == "_"):
            start -= 1
        while end < len(text) and (text[end].isalnum() or text[end] == "_"):
            end += 1
        return start, end

    @staticmethod
    def _merge_adjacent_model_detections(
        text: str,
        detections: list[CanonicalDetection],
    ) -> list[CanonicalDetection]:
        merged: list[CanonicalDetection] = []
        for current in sorted(detections, key=lambda item: (item.start, item.end)):
            previous = merged[-1] if merged else None
            if (
                previous
                and previous.end == current.start
                and previous.canonical_type == current.canonical_type
                and previous.provenance.native_entity_type
                == current.provenance.native_entity_type
                and previous.provenance.model_id == current.provenance.model_id
            ):
                merged[-1] = CanonicalDetection(
                    canonical_type=previous.canonical_type,
                    text=text[previous.start : current.end],
                    start=previous.start,
                    end=current.end,
                    confidence=min(previous.confidence, current.confidence),
                    provenance=previous.provenance,
                )
            else:
                merged.append(current)
        return merged
