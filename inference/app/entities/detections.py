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
