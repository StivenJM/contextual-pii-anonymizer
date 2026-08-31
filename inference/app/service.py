from typing import Any

import bentoml

from app.schemas.inference import (
    DetectionResponse,
    InferenceRequest,
    InferenceResponse,
)
from app.services.implementations.openmed import OpenMedModel
from app.use_cases.inference import DetectPiiUseCase, InferenceResult


def to_response(result: InferenceResult) -> InferenceResponse:
    return InferenceResponse(
        model_id=result.model_id,
        detections=[
            DetectionResponse(
                native_type=detection.native_type,
                text=detection.text,
                start=detection.start,
                end=detection.end,
                confidence=detection.confidence,
            )
            for detection in result.detections
        ],
    )


@bentoml.service(
    resources={"cpu": "2"},
    traffic={"timeout": 120},
)
class PiiInferenceService:
    def __init__(self) -> None:
        model = OpenMedModel()
        self.detect_pii = DetectPiiUseCase(model=model)

    @bentoml.api(input_spec=InferenceRequest, output_spec=InferenceResponse)
    def detect(self, **params: Any) -> InferenceResponse:
        request = InferenceRequest(**params)
        result = self.detect_pii.execute(request.text)
        return to_response(result)
