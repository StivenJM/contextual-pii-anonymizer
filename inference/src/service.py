import bentoml
from typing import Any

from controllers.dtos.analyze_dto import AnalyzeRequest, AnalyzeResponse
from use_cases.pii_usecases import PiiAnalyzer


@bentoml.service(
    resources={"cpu": "2"},
    traffic={"timeout": 120},
)
class PiiInferenceService:
    def __init__(self) -> None:
        self.analyzer = PiiAnalyzer()

    @bentoml.api(input_spec=AnalyzeRequest, output_spec=AnalyzeResponse)
    def analyze(self, **params: Any) -> AnalyzeResponse:
        request = AnalyzeRequest(**params)
        return self.analyzer.analyze(request)
