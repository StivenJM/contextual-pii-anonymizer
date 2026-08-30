import re
from typing import Any

from controllers.dtos.analyze_dto import AnalyzeRequest, AnalyzeResponse, DetectedEntity


MODEL_ID = "OpenMed/OpenMed-PII-Spanish-QwenMed-XLarge-600M-v1"
EMAIL_PATTERN = re.compile(r"[\w.!#$%&'*+/=?^_`{|}~-]+@[\w-]+(?:\.[\w-]+)+")
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+593\s?)?(?:0\s?)?9\d{1}[\s-]?\d{3}[\s-]?\d{4}(?!\d)")
ECUADORIAN_ID_PATTERN = re.compile(r"(?<!\d)\d{10}(?!\d)")


class PiiAnalyzer:
    def __init__(self, model_id: str = MODEL_ID) -> None:
        self.model_id = model_id
        self.pipeline = self._load_pipeline(model_id)

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        raw_entities = self.pipeline(request.text)
        model_entities = [self._to_entity(entity, request.text) for entity in raw_entities]
        regex_entities = self._detect_regex_entities(request.text)
        entities = self._deduplicate_entities(
            self._merge_entities(model_entities + regex_entities, request.text)
        )

        return AnalyzeResponse(
            text=request.text,
            entities=entities,
            model_version=self.model_id,
        )

    def _load_pipeline(self, model_id: str) -> Any:
        try:
            import torch
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "Missing inference dependencies. Install them with: "
                "python -m pip install -e ."
            ) from exc

        device = 0 if torch.cuda.is_available() else -1

        return pipeline(
            task="token-classification",
            model=model_id,
            tokenizer=model_id,
            aggregation_strategy="simple",
            device=device,
            trust_remote_code=True,
        )

    def _to_entity(self, entity: dict[str, Any], source_text: str) -> DetectedEntity:
        start = int(entity.get("start", 0))
        end = int(entity.get("end", start))
        text = source_text[start:end] or str(entity.get("word", ""))

        return DetectedEntity(
            type=self._normalize_label(entity),
            text=text,
            start=start,
            end=end,
            confidence=round(float(entity.get("score", 0.0)), 4),
            source="model",
        )

    def _normalize_label(self, entity: dict[str, Any]) -> str:
        label = str(entity.get("entity_group") or entity.get("entity") or "UNKNOWN")
        return label.removeprefix("B-").removeprefix("I-").upper()

    def _detect_regex_entities(self, text: str) -> list[DetectedEntity]:
        entities: list[DetectedEntity] = []

        entities.extend(self._find_regex_entities(text, EMAIL_PATTERN, "EMAIL"))
        entities.extend(self._find_regex_entities(text, PHONE_PATTERN, "PH"))
        entities.extend(self._find_regex_entities(text, ECUADORIAN_ID_PATTERN, "ID"))

        return entities

    def _find_regex_entities(
        self,
        text: str,
        pattern: re.Pattern[str],
        entity_type: str,
    ) -> list[DetectedEntity]:
        return [
            DetectedEntity(
                type=entity_type,
                text=match.group(0),
                start=match.start(),
                end=match.end(),
                confidence=1.0,
                source="regex",
            )
            for match in pattern.finditer(text)
        ]

    def _merge_entities(
        self,
        entities: list[DetectedEntity],
        source_text: str,
    ) -> list[DetectedEntity]:
        if not entities:
            return []

        ordered_entities = sorted(entities, key=lambda entity: (entity.start, entity.end))
        merged_entities: list[DetectedEntity] = []

        for entity in ordered_entities:
            if not merged_entities:
                merged_entities.append(entity)
                continue

            previous = merged_entities[-1]
            same_type = previous.type == entity.type
            same_source = previous.source == entity.source
            contiguous_or_overlapping = entity.start <= previous.end

            if not same_type or not same_source or not contiguous_or_overlapping:
                merged_entities.append(entity)
                continue

            start = previous.start
            end = max(previous.end, entity.end)
            merged_entities[-1] = DetectedEntity(
                type=previous.type,
                text=source_text[start:end],
                start=start,
                end=end,
                confidence=round(min(previous.confidence, entity.confidence), 4),
                source=previous.source,
            )

        return merged_entities

    def _deduplicate_entities(self, entities: list[DetectedEntity]) -> list[DetectedEntity]:
        deduplicated: list[DetectedEntity] = []

        for entity in sorted(entities, key=lambda item: (item.start, item.end)):
            overlapping_index = self._find_overlapping_index(deduplicated, entity)

            if overlapping_index is None:
                deduplicated.append(entity)
                continue

            existing = deduplicated[overlapping_index]
            if self._should_replace_existing(existing, entity):
                deduplicated[overlapping_index] = entity

        return sorted(deduplicated, key=lambda item: (item.start, item.end))

    def _find_overlapping_index(
        self,
        entities: list[DetectedEntity],
        candidate: DetectedEntity,
    ) -> int | None:
        for index, entity in enumerate(entities):
            if candidate.start < entity.end and entity.start < candidate.end:
                return index
        return None

    def _should_replace_existing(
        self,
        existing: DetectedEntity,
        candidate: DetectedEntity,
    ) -> bool:
        if existing.source != "regex" and candidate.source == "regex":
            return True
        if existing.source == candidate.source:
            existing_length = existing.end - existing.start
            candidate_length = candidate.end - candidate.start
            return candidate_length > existing_length
        return False
