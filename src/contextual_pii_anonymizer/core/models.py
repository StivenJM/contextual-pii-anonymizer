"""Shared data structures for the contextual anonymizer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Entity:
    text: str
    entity_type: str
    start: int
    end: int
    source: str
    confidence: float | None = None
    sources: list[str] = field(default_factory=list)
    sensitivity: str | None = None
    weight: int | None = None
    action: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.sources:
            self.sources = [self.source]

    @property
    def length(self) -> int:
        return self.end - self.start

    def overlaps(self, other: "Entity") -> bool:
        return not (self.end <= other.start or self.start >= other.end)

    def to_dict(self) -> dict:
        return {
            "texto": self.text,
            "tipo": self.entity_type,
            "inicio": self.start,
            "fin": self.end,
            "fuente": self.source,
            "fuentes": self.sources,
            "confianza": self.confidence,
            "sensibilidad": self.sensitivity,
            "peso": self.weight,
            "accion": self.action,
            "razon": self.reason,
        }
