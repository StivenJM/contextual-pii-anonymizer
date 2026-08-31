from collections.abc import Iterable

from app.entities.models import ModelMetadata
from app.services.pii_model import PiiDetectionModel


class ModelNotAvailableError(LookupError):
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id
        super().__init__(f"Model '{model_id}' is not available.")


class ModelCatalog:
    def __init__(self, models: Iterable[PiiDetectionModel]) -> None:
        self._models: dict[str, PiiDetectionModel] = {}
        for model in models:
            model_id = model.metadata.id
            if model_id in self._models:
                raise ValueError(f"Duplicate model id: '{model_id}'.")
            self._models[model_id] = model

    def list_models(self) -> tuple[ModelMetadata, ...]:
        return tuple(
            self._models[model_id].metadata for model_id in sorted(self._models)
        )

    def get_metadata(self, model_id: str) -> ModelMetadata:
        return self.resolve(model_id).metadata

    def resolve(self, model_id: str) -> PiiDetectionModel:
        try:
            return self._models[model_id]
        except KeyError as exc:
            raise ModelNotAvailableError(model_id) from exc
