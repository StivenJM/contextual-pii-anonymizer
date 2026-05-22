"""End-to-end pipeline for the contextual anonymizer."""

from __future__ import annotations

from contextual_pii_anonymizer.anonymization import anonymize
from contextual_pii_anonymizer.context import decide_sensitivity
from contextual_pii_anonymizer.detection import detect_with_model, detect_with_rules
from contextual_pii_anonymizer.processing.fusion import merge_entities


def process_text(text: str, ner_pipeline=None) -> dict:
    original = text.strip()
    rule_entities = detect_with_rules(original)
    model_entities = detect_with_model(original, ner_pipeline)
    entities = merge_entities(rule_entities, model_entities)
    entities = decide_sensitivity(entities, original)
    anonymized_text, replacements = anonymize(original, entities)

    return {
        "original": original,
        "salida": anonymized_text,
        "entidades": [entity.to_dict() for entity in entities],
        "reemplazos": replacements,
        "indice_exposicion_original": sum(entity.weight or 0 for entity in entities),
        "indice_exposicion_salida": 0,
    }
