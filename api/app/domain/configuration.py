from dataclasses import dataclass, field
from enum import StrEnum

from app.domain.detections import DetectionSource


class ProtectionAction(StrEnum):
    KEEP = "KEEP"
    MASK = "MASK"
    REPLACE_WITH_LABEL = "REPLACE_WITH_LABEL"
    PSEUDONYMIZE = "PSEUDONYMIZE"


@dataclass(frozen=True)
class PatternRecognizer:
    id: int | None
    name: str
    canonical_type: str
    patterns: tuple[str, ...]
    score: float
    context_words: tuple[str, ...] = ()
    validator: str | None = None
    enabled: bool = True


@dataclass(frozen=True)
class GazetteerEntry:
    id: int | None
    value: str


@dataclass(frozen=True)
class Gazetteer:
    id: int | None
    name: str
    canonical_type: str
    score: float = 0.85
    case_sensitive: bool = False
    enabled: bool = True
    entries: tuple[GazetteerEntry, ...] = ()


@dataclass(frozen=True)
class DetectionSettings:
    threshold: float = 0.5
    model_enabled: bool = True
    pattern_enabled: bool = True
    gazetteer_enabled: bool = True
    source_priority: tuple[DetectionSource, ...] = field(
        default_factory=lambda: (
            DetectionSource.PATTERN,
            DetectionSource.GAZETTEER,
            DetectionSource.MODEL,
        )
    )

    def enabled_sources(self) -> set[DetectionSource]:
        enabled: set[DetectionSource] = set()
        if self.model_enabled:
            enabled.add(DetectionSource.MODEL)
        if self.pattern_enabled:
            enabled.add(DetectionSource.PATTERN)
        if self.gazetteer_enabled:
            enabled.add(DetectionSource.GAZETTEER)
        return enabled


@dataclass(frozen=True)
class ProtectionRule:
    id: int | None
    canonical_type: str
    action: ProtectionAction


@dataclass(frozen=True)
class ModelMapping:
    id: int | None
    model_id: str
    native_entity_type: str
    canonical_type: str
