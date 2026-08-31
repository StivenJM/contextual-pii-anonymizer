from controllers.dtos.inference_dto import (
    InferenceRequest,
    InferenceResponse,
    ModelDetection,
)
from models.openmed import OpenMedModel


class ModelInference:
    def __init__(self, model: OpenMedModel | None = None) -> None:
        self.model = model or OpenMedModel()

    def detect(self, request: InferenceRequest) -> InferenceResponse:
        detections = [
            ModelDetection(
                native_type=detection.native_type,
                text=detection.text,
                start=detection.start,
                end=detection.end,
                confidence=detection.confidence,
            )
            for detection in self.model.detect(request.text)
        ]

        return InferenceResponse(
            model_id=self.model.model_id,
            detections=detections,
        )
