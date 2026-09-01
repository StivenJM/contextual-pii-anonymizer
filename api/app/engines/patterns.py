import re

from app.domain.configuration import PatternRecognizer
from app.domain.detections import CanonicalDetection, DetectionSource, Provenance
from app.engines.validators import VALIDATORS


class PatternRecognizerEngine:
    def detect(
        self,
        text: str,
        recognizers: list[PatternRecognizer],
    ) -> list[CanonicalDetection]:
        detections: list[CanonicalDetection] = []
        for recognizer in recognizers:
            if not recognizer.enabled:
                continue
            validator = VALIDATORS.get(recognizer.validator) if recognizer.validator else None
            if recognizer.validator and validator is None:
                raise ValueError(f"Unknown validator: {recognizer.validator}")
            for pattern in recognizer.patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    matched_text = match.group(0)
                    if validator and not validator(matched_text):
                        continue
                    confidence = recognizer.score
                    if recognizer.context_words:
                        context = text[max(0, match.start() - 60) : match.end() + 60].casefold()
                        if any(word.casefold() in context for word in recognizer.context_words):
                            confidence = min(1.0, confidence + 0.1)
                    detections.append(
                        CanonicalDetection(
                            canonical_type=recognizer.canonical_type,
                            text=matched_text,
                            start=match.start(),
                            end=match.end(),
                            confidence=confidence,
                            provenance=Provenance(
                                source=DetectionSource.PATTERN,
                                source_id=str(recognizer.id or recognizer.name),
                            ),
                        )
                    )
        return detections
