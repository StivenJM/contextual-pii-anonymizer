from typing import Any

import bentoml

from controllers.dtos.inference_dto import InferenceRequest, InferenceResponse
from use_cases.model_inference import ModelInference


@bentoml.service(
    resources={"cpu": "2"},
    traffic={"timeout": 120},
)
class PiiInferenceService:
    def __init__(self) -> None:
        self.inference = ModelInference()

    @bentoml.api(input_spec=InferenceRequest, output_spec=InferenceResponse)
    def detect(self, **params: Any) -> InferenceResponse:
        request = InferenceRequest(**params)
        return self.inference.detect(request)
