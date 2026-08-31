from typing import Protocol

from app.entities.detections import Detection


class PiiDetectionModel(Protocol):
    model_id: str

    def detect(self, text: str) -> list[Detection]:
        ...
