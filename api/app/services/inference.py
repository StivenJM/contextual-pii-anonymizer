from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ModelMetadata:
    id: str
    name: str
    version: str
    description: str
    native_entity_types: tuple[str, ...]


@dataclass(frozen=True)
class NativeDetection:
    native_type: str
    text: str
    start: int
    end: int
    confidence: float


@dataclass(frozen=True)
class NativeInferenceResult:
    model_id: str
    model_version: str
    detections: tuple[NativeDetection, ...]


class InferenceService(Protocol):
    async def list_models(self) -> list[ModelMetadata]: ...
    async def get_model(self, model_id: str) -> ModelMetadata: ...
    async def detect(self, model_id: str, text: str) -> NativeInferenceResult: ...
