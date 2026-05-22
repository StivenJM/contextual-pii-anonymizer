"""Rule-based detectors for Ecuadorian and academic sensitive data."""

from __future__ import annotations

import re

from contextual_pii_anonymizer.core import Entity
from contextual_pii_anonymizer.detection.validators import is_valid_ec_cedula, is_valid_ec_ruc

EMAIL_RE = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+593\s?)?(?:0?9\d{8}|0[2-7]\d{7})(?!\d)")
CEDULA_RE = re.compile(r"(?<!\d)\d{10}(?!\d)")
RUC_RE = re.compile(r"(?<!\d)\d{13}(?!\d)")
INSTITUTIONAL_USER_RE = re.compile(r"\b[a-z][a-z0-9._-]{3,}\d{2,4}\b", re.IGNORECASE)
GRADE_RE = re.compile(r"(?<!\d)(?:10(?:\.0)?|[0-9](?:\.\d{1,2})?)(?!\d)")

ACADEMIC_KEYWORDS = {
    "aula virtual",
    "calculo ii",
    "campus",
    "carrera",
    "clases",
    "docente",
    "examen",
    "facultad",
    "matricula",
    "materia",
    "proyecto final",
    "recalificacion",
    "secretaria academica",
    "semestre",
    "sistema academico",
    "universidad",
}

FINANCIAL_KEYWORDS = {
    "beca",
    "cuenta bancaria",
    "deuda",
    "pago",
    "prorroga de pago",
    "situacion economica",
    "tarjeta",
}

HEALTH_KEYWORDS = {
    "ansiedad",
    "certificado medico",
    "diagnostico",
    "discapacidad",
    "esta enferma",
    "tratamiento",
}

ROUTINE_PATTERNS = [
    re.compile(r"\btodos los dias\b[^.]{0,60}", re.IGNORECASE),
    re.compile(r"\bsalgo a las\s+\d{1,2}:\d{2}\b", re.IGNORECASE),
]

INSTITUTIONAL_DOMAINS = (".edu.ec", "universidad.edu.ec")


def detect_with_rules(text: str) -> list[Entity]:
    entities: list[Entity] = []

    for match in EMAIL_RE.finditer(text):
        email = match.group(0)
        entity_type = "CORREO_INSTITUCIONAL" if email.lower().endswith(INSTITUTIONAL_DOMAINS) else "CORREO"
        entities.append(Entity(email, entity_type, match.start(), match.end(), "regla_correo"))

    for match in RUC_RE.finditer(text):
        value = match.group(0)
        if is_valid_ec_ruc(value):
            entities.append(Entity(value, "RUC_EC", match.start(), match.end(), "regla_ruc"))

    for match in CEDULA_RE.finditer(text):
        value = match.group(0)
        if is_valid_ec_cedula(value):
            entities.append(Entity(value, "CEDULA_EC", match.start(), match.end(), "regla_cedula"))

    for match in PHONE_RE.finditer(text):
        entities.append(Entity(match.group(0), "TELEFONO_EC", match.start(), match.end(), "regla_telefono"))

    for match in INSTITUTIONAL_USER_RE.finditer(text):
        token = match.group(0)
        if "@" not in token and not token.isdigit():
            entities.append(Entity(token, "USUARIO_INSTITUCIONAL", match.start(), match.end(), "regla_usuario"))

    entities.extend(_detect_keyword_entities(text, ACADEMIC_KEYWORDS, "DATO_ACADEMICO", "diccionario_academico"))
    entities.extend(_detect_keyword_entities(text, FINANCIAL_KEYWORDS, "DATO_FINANCIERO", "diccionario_financiero"))
    entities.extend(_detect_keyword_entities(text, HEALTH_KEYWORDS, "SALUD", "diccionario_salud"))
    entities.extend(_detect_routines(text))
    entities.extend(_detect_grades(text))
    entities.extend(_detect_probable_names(text))

    return sorted(entities, key=lambda entity: (entity.start, -entity.length))


def _detect_keyword_entities(text: str, keywords: set[str], entity_type: str, source: str) -> list[Entity]:
    entities = []
    for keyword in keywords:
        pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            entities.append(Entity(match.group(0), entity_type, match.start(), match.end(), source))
    return entities


def _detect_routines(text: str) -> list[Entity]:
    entities = []
    for pattern in ROUTINE_PATTERNS:
        for match in pattern.finditer(text):
            entities.append(Entity(match.group(0).strip(), "RUTINA", match.start(), match.end(), "regla_rutina"))
    return entities


def _detect_grades(text: str) -> list[Entity]:
    entities = []
    context_words = ("nota", "saque", "reprobe", "examen", "calificacion", "promedio")
    for match in GRADE_RE.finditer(text):
        window = text[max(0, match.start() - 40) : min(len(text), match.end() + 40)].lower()
        if any(word in window for word in context_words):
            entities.append(Entity(match.group(0), "NOTA", match.start(), match.end(), "regla_nota"))
    return entities


def _detect_probable_names(text: str) -> list[Entity]:
    # TODO: pending research - replace this heuristic with the selected NER model or fine-tuned detector.
    triggers = [
        r"\bme llamo\s+",
        r"\bmi nombre es\s+",
        r"\bsoy\s+",
        r"\bla docente\s+",
    ]
    name_pattern = r"([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3})"
    entities = []
    for trigger in triggers:
        pattern = re.compile(f"(?i:{trigger})" + name_pattern)
        for match in pattern.finditer(text):
            start, end = match.span(1)
            entities.append(Entity(text[start:end], "PERSONA", start, end, "heuristica_nombre"))
    return entities
