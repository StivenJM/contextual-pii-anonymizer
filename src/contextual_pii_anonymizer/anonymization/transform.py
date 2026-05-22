"""Semantic transformation of sensitive entities."""

from __future__ import annotations

from collections import defaultdict

from contextual_pii_anonymizer.core import Entity


def anonymize(text: str, entities: list[Entity]) -> tuple[str, list[dict[str, str]]]:
    counters: defaultdict[str, int] = defaultdict(int)
    replacements = []

    for entity in sorted(entities, key=lambda item: item.start):
        if entity.action != "transformar":
            continue
        counters[entity.entity_type] += 1
        replacement = f"<{entity.entity_type}_{counters[entity.entity_type]}>"
        replacements.append(
            {
                "inicio": entity.start,
                "fin": entity.end,
                "texto": entity.text,
                "reemplazo": replacement,
                "tipo": entity.entity_type,
            }
        )

    transformed = text
    for replacement in sorted(replacements, key=lambda item: item["inicio"], reverse=True):
        transformed = transformed[: replacement["inicio"]] + replacement["reemplazo"] + transformed[replacement["fin"] :]

    return transformed, replacements
