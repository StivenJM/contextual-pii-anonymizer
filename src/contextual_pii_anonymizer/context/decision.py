"""Contextual sensitivity decision layer."""

from __future__ import annotations

from contextual_pii_anonymizer.core import Entity
from contextual_pii_anonymizer.context.taxonomy import SENSITIVITY_WEIGHTS, sensitivity_for

CRITICAL_CONTEXT = ("salud", "ansiedad", "certificado medico", "deuda", "beca", "cuenta bancaria", "pago")
ACADEMIC_CONTEXT = ("nota", "matricula", "reprobe", "examen", "carrera", "semestre", "aula virtual")


def decide_sensitivity(entities: list[Entity], text: str) -> list[Entity]:
    has_person = any(entity.entity_type == "PERSONA" for entity in entities)
    has_direct_identifier = any(entity.entity_type in {"CEDULA_EC", "RUC_EC", "CORREO", "TELEFONO_EC"} for entity in entities)
    lowered_text = text.lower()

    for entity in entities:
        sensitivity, weight, reason = sensitivity_for(entity.entity_type)
        window = _context_window(lowered_text, entity.start, entity.end)

        if entity.entity_type == "CORREO_INSTITUCIONAL" and (has_person or any(word in window for word in ACADEMIC_CONTEXT)):
            sensitivity, reason = "alta", "Correo institucional combinado con contexto academico o personal"
        elif entity.entity_type in {"DATO_ACADEMICO", "INSTITUCION"} and has_person:
            sensitivity, reason = "alta", "Dato academico o institucional asociado a una persona"
        elif entity.entity_type == "PERSONA" and has_direct_identifier:
            sensitivity, reason = "alta", "Persona asociada con identificadores directos"
        elif any(word in window for word in CRITICAL_CONTEXT) and entity.entity_type in {"PERSONA", "DATO_ACADEMICO"}:
            sensitivity, reason = "critica", "Entidad asociada a contexto financiero o de salud"

        entity.sensitivity = sensitivity
        entity.weight = SENSITIVITY_WEIGHTS[sensitivity]
        entity.reason = reason
        entity.action = recommended_action(sensitivity)

    return entities


def recommended_action(sensitivity: str) -> str:
    if sensitivity == "critica":
        # TODO: pending research - validate whether critical cases should be blocked or only transformed.
        return "transformar"
    if sensitivity in {"alta", "media"}:
        return "transformar"
    return "mantener"


def _context_window(text: str, start: int, end: int, size: int = 80) -> str:
    return text[max(0, start - size) : min(len(text), end + size)]
