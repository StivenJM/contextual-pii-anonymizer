from dataclasses import dataclass

from app.entities.detections import Detection
from app.services.pii_model import PiiDetectionModel


@dataclass(frozen=True)
class InferenceResult:
    model_id: str
    detections: list[Detection]


@dataclass(frozen=True)
class DetectPiiUseCase:
    model: PiiDetectionModel

    def execute(self, text: str) -> InferenceResult:
        return InferenceResult(
            model_id=self.model.model_id,
            detections=self.model.detect(text),
        )
