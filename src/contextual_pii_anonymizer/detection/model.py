"""Optional NER model detector adapter."""

from __future__ import annotations

from contextual_pii_anonymizer.context import normalize_label
from contextual_pii_anonymizer.core import Entity


def detect_with_model(text: str, ner_pipeline=None) -> list[Entity]:
    if ner_pipeline is None:
        return []

    results = ner_pipeline(text)
    entities = []
    for result in results:
        label = result.get("entity_group") or result.get("entity") or ""
        entities.append(
            Entity(
                text=result["word"],
                entity_type=normalize_label(label),
                start=result["start"],
                end=result["end"],
                source="modelo_ner",
                confidence=float(result["score"]) if "score" in result else None,
            )
        )

    return entities
