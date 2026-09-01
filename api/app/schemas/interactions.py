from pydantic import BaseModel, Field

from app.domain.configuration import ProtectionAction
from app.domain.detections import DetectionSource


class ProtectInteractionRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)


class ProvenanceResponse(BaseModel):
    source: DetectionSource
    source_id: str | None = None
    model_id: str | None = None
    model_version: str | None = None
    native_entity_type: str | None = None


class DetectionResponse(BaseModel):
    canonical_type: str
    text: str
    start: int
    end: int
    confidence: float
    provenance: ProvenanceResponse


class OperationResponse(BaseModel):
    canonical_type: str | None
    start: int
    end: int
    original_text: str
    replacement: str
    action: ProtectionAction
    mapping_gap: bool


class MappingGapResponse(BaseModel):
    text: str
    start: int
    end: int
    confidence: float
    model_id: str
    model_version: str
    native_entity_type: str


class ProtectInteractionResponse(BaseModel):
    original_text: str
    protected_text: str
    detections: list[DetectionResponse]
    operations: list[OperationResponse]
    mapping_gaps: list[MappingGapResponse]
    warnings: list[str]
