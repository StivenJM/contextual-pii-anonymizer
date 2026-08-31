from dataclasses import dataclass


@dataclass(frozen=True)
class Detection:
    native_type: str
    text: str
    start: int
    end: int
    confidence: float

    def __post_init__(self) -> None:
        if not self.native_type:
            raise ValueError("Detection type must not be empty.")
        if self.start < 0 or self.end < self.start:
            raise ValueError("Detection span is invalid.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Detection confidence must be between 0 and 1.")


@dataclass(frozen=True)
class ModelMetadata:
    id: str
    name: str
    version: str
    description: str
    native_entity_types: tuple[str, ...]

    def __post_init__(self) -> None:
        text_fields = (self.id, self.name, self.version, self.description)
        if any(not value.strip() for value in text_fields):
            raise ValueError("Model metadata text fields must not be blank.")
        if not self.native_entity_types:
            raise ValueError("A model must declare at least one native entity type.")
        if any(not entity_type.strip() for entity_type in self.native_entity_types):
            raise ValueError("Native entity types must not be blank.")
        if len(set(self.native_entity_types)) != len(self.native_entity_types):
            raise ValueError("Native entity types must be unique.")
