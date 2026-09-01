from pydantic import BaseModel, ConfigDict, Field

from app.domain.configuration import ProtectionAction
from app.domain.detections import DetectionSource


class ModelMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    version: str
    description: str
    native_entity_types: list[str] | tuple[str, ...]


class ActiveModelRequest(BaseModel):
    model_id: str = Field(min_length=1)


class MappingRequest(BaseModel):
    native_entity_type: str = Field(min_length=1)
    canonical_type: str = Field(min_length=1)


class MappingUpdateRequest(MappingRequest):
    model_id: str = Field(min_length=1)


class MappingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    model_id: str
    native_entity_type: str
    canonical_type: str


class PatternRequest(BaseModel):
    name: str = Field(min_length=1)
    canonical_type: str = Field(min_length=1)
    patterns: list[str] = Field(min_length=1)
    score: float = Field(ge=0, le=1)
    context_words: list[str] = []
    validator: str | None = None
    enabled: bool = True


class EnabledRequest(BaseModel):
    enabled: bool


class PatternResponse(PatternRequest):
    model_config = ConfigDict(from_attributes=True)
    id: int


class GazetteerRequest(BaseModel):
    name: str = Field(min_length=1)
    canonical_type: str = Field(min_length=1)
    score: float = Field(default=0.85, ge=0, le=1)
    case_sensitive: bool = False
    enabled: bool = True


class GazetteerEntryRequest(BaseModel):
    value: str = Field(min_length=1)


class GazetteerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    value: str


class GazetteerResponse(GazetteerRequest):
    model_config = ConfigDict(from_attributes=True)
    id: int
    entries: list[GazetteerEntryResponse] | tuple[GazetteerEntryResponse, ...] = []


class DetectionSettingsRequest(BaseModel):
    threshold: float = Field(ge=0, le=1)
    model_enabled: bool
    pattern_enabled: bool
    gazetteer_enabled: bool
    source_priority: list[DetectionSource]


class DetectionSettingsResponse(DetectionSettingsRequest):
    model_config = ConfigDict(from_attributes=True)


class ProtectionRuleRequest(BaseModel):
    canonical_type: str = Field(min_length=1)
    action: ProtectionAction


class ProtectionRuleResponse(ProtectionRuleRequest):
    model_config = ConfigDict(from_attributes=True)
    id: int
