"""Entity fusion and overlap resolution."""

from __future__ import annotations

from contextual_pii_anonymizer.core import Entity

STRUCTURED_PRIORITY = {
    "CEDULA_EC",
    "RUC_EC",
    "CORREO",
    "CORREO_INSTITUCIONAL",
    "TELEFONO_EC",
    "USUARIO_INSTITUCIONAL",
}


def merge_entities(*entity_groups: list[Entity]) -> list[Entity]:
    candidates = [entity for group in entity_groups for entity in group]
    candidates.sort(key=lambda entity: (entity.start, -_priority(entity), -entity.length))

    merged: list[Entity] = []
    for candidate in candidates:
        overlap_index = next((index for index, entity in enumerate(merged) if entity.overlaps(candidate)), None)
        if overlap_index is None:
            merged.append(candidate)
            continue

        current = merged[overlap_index]
        winner = _choose_winner(current, candidate)
        loser = candidate if winner is current else current
        winner.sources = sorted(set(winner.sources + loser.sources))
        merged[overlap_index] = winner

    return sorted(merged, key=lambda entity: entity.start)


def _choose_winner(left: Entity, right: Entity) -> Entity:
    left_score = (_priority(left), left.length)
    right_score = (_priority(right), right.length)
    return right if right_score > left_score else left


def _priority(entity: Entity) -> int:
    return 2 if entity.entity_type in STRUCTURED_PRIORITY else 1
