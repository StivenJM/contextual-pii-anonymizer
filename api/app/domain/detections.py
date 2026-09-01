from dataclasses import dataclass
from enum import StrEnum

from app.domain.taxonomy import is_valid_type


class DetectionSource(StrEnum):
    MODEL = "MODEL"
    PATTERN = "PATTERN"
    GAZETTEER = "GAZETTEER"


@dataclass(frozen=True)
class Provenance:
    source: DetectionSource
    source_id: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    native_entity_type: str | None = None


@dataclass(frozen=True)
class CanonicalDetection:
    canonical_type: str
    text: str
    start: int
    end: int
    confidence: float
    provenance: Provenance

    def __post_init__(self) -> None:
        if not is_valid_type(self.canonical_type):
            raise ValueError(f"Unknown canonical entity type: {self.canonical_type}")
        if self.start < 0 or self.end <= self.start:
            raise ValueError("Detection must have a non-empty valid span.")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Detection confidence must be between 0 and 1.")


@dataclass(frozen=True)
class MappingGap:
    text: str
    start: int
    end: int
    confidence: float
    model_id: str
    model_version: str
    native_entity_type: str

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError("Mapping gap must have a non-empty valid span.")
