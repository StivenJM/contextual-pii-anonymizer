from dataclasses import dataclass

from app.entities.models import Detection, ModelMetadata
from app.model_catalog import ModelCatalog


@dataclass(frozen=True)
class InferenceResult:
    model_id: str
    model_version: str
    detections: list[Detection]


@dataclass(frozen=True)
class DetectPiiUseCase:
    catalog: ModelCatalog

    def execute(self, model_id: str, text: str) -> InferenceResult:
        model = self.catalog.resolve(model_id)
        return InferenceResult(
            model_id=model.metadata.id,
            model_version=model.metadata.version,
            detections=model.detect(text),
        )


@dataclass(frozen=True)
class DiscoverModelsUseCase:
    catalog: ModelCatalog

    def execute(self) -> tuple[ModelMetadata, ...]:
        return self.catalog.list_models()
