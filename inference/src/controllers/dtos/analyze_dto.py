from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, description="Text to analyze for PII entities.")


class DetectedEntity(BaseModel):
    type: str
    text: str
    start: int
    end: int
    confidence: float
    source: str


class AnalyzeResponse(BaseModel):
    text: str
    entities: list[DetectedEntity]
    model_version: str
