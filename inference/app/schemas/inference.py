from pydantic import BaseModel, Field, field_validator, model_validator


class InferenceRequest(BaseModel):
    text: str = Field(
        min_length=1,
        strict=True,
        description="Text to process with the ML model.",
    )

    @field_validator("text")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text must contain at least one non-whitespace character.")
        return value


class DetectionResponse(BaseModel):
    native_type: str = Field(min_length=1)
    text: str
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_span(self) -> "DetectionResponse":
        if self.end < self.start:
            raise ValueError("Detection end must be greater than or equal to start.")
        return self


class InferenceResponse(BaseModel):
    model_id: str = Field(min_length=1)
    detections: list[DetectionResponse]
