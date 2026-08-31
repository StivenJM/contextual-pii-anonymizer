from typing import Protocol

from app.entities.models import Detection, ModelMetadata


class PiiDetectionModel(Protocol):
    @property
    def metadata(self) -> ModelMetadata:
        ...

    def detect(self, text: str) -> list[Detection]:
        ...
