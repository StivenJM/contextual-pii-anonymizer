"""Project taxonomy and sensitivity defaults."""

from __future__ import annotations

SENSITIVITY_WEIGHTS = {
    "baja": 1,
    "media": 2,
    "alta": 3,
    "critica": 4,
}

BASE_SENSITIVITY = {
    "PERSONA": ("alta", "Nombre de persona"),
    "CEDULA_EC": ("alta", "Identificador personal ecuatoriano"),
    "RUC_EC": ("alta", "Identificador tributario ecuatoriano"),
    "CORREO": ("alta", "Correo electronico identificable"),
    "CORREO_INSTITUCIONAL": ("media", "Correo institucional identificable"),
    "TELEFONO_EC": ("alta", "Telefono identificable"),
    "USUARIO_INSTITUCIONAL": ("alta", "Usuario institucional identificable"),
    "CODIGO_ACADEMICO": ("media", "Codigo o referencia academica"),
    "DATO_ACADEMICO": ("media", "Informacion academica contextual"),
    "DATO_FINANCIERO": ("critica", "Informacion financiera sensible"),
    "SALUD": ("critica", "Informacion de salud sensible"),
    "RUTINA": ("alta", "Rutina o patron personal"),
    "UBICACION": ("media", "Ubicacion contextual"),
    "INSTITUCION": ("media", "Institucion o dependencia"),
    "ORGANIZACION": ("media", "Organizacion mencionada"),
    "MATERIA": ("media", "Materia o asignatura academica"),
    "NOTA": ("alta", "Calificacion asociable a una persona"),
}

MODEL_LABEL_MAP = {
    "PER": "PERSONA",
    "PERSON": "PERSONA",
    "PERSONA": "PERSONA",
    "NAME": "PERSONA",
    "NOMBRE": "PERSONA",
    "LOC": "UBICACION",
    "LOCATION": "UBICACION",
    "UBICACION": "UBICACION",
    "ORG": "INSTITUCION",
    "ORGANIZATION": "INSTITUCION",
    "ORGANISATION": "INSTITUCION",
    "INSTITUCION": "INSTITUCION",
    "EMAIL": "CORREO",
    "PHONE": "TELEFONO_EC",
}


def normalize_label(label: str) -> str:
    """Map model-specific labels into the project taxonomy."""
    clean_label = label.upper().replace("B-", "").replace("I-", "")
    return MODEL_LABEL_MAP.get(clean_label, clean_label)


def sensitivity_for(entity_type: str) -> tuple[str, int, str]:
    sensitivity, reason = BASE_SENSITIVITY.get(
        entity_type,
        ("media", "Entidad pendiente de ajuste en la taxonomia"),
    )
    return sensitivity, SENSITIVITY_WEIGHTS[sensitivity], reason
