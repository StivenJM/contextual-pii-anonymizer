from http import HTTPStatus
from typing import Any

import bentoml
from bentoml.exceptions import BentoMLException

from app.entities.models import ModelMetadata
from app.model_catalog import ModelCatalog, ModelNotAvailableError
from app.schemas.inference import (
    DetectionResponse,
    InferenceRequest,
    InferenceResponse,
    ModelDiscoveryResponse,
    ModelMetadataResponse,
)
from app.services.implementations.openmed import OpenMedModel
from app.use_cases.inference import (
    DetectPiiUseCase,
    DiscoverModelsUseCase,
    InferenceResult,
)


class ModelNotFoundTransportError(BentoMLException):
    error_code = HTTPStatus.NOT_FOUND


def to_inference_response(result: InferenceResult) -> InferenceResponse:
    return InferenceResponse(
        model_id=result.model_id,
        model_version=result.model_version,
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


def to_metadata_response(metadata: ModelMetadata) -> ModelMetadataResponse:
    return ModelMetadataResponse(
        id=metadata.id,
        name=metadata.name,
        version=metadata.version,
        description=metadata.description,
        native_entity_types=list(metadata.native_entity_types),
    )


@bentoml.service(
    resources={"cpu": "2"},
    traffic={"timeout": 120},
)
class PiiInferenceService:
    def __init__(self) -> None:
        model = OpenMedModel()
        catalog = ModelCatalog([model])
        self.detect_pii = DetectPiiUseCase(catalog=catalog)
        self.discover_models = DiscoverModelsUseCase(catalog=catalog)

    @bentoml.api(output_spec=ModelDiscoveryResponse)
    def models(self) -> ModelDiscoveryResponse:
        return ModelDiscoveryResponse(
            models=[
                to_metadata_response(metadata)
                for metadata in self.discover_models.execute()
            ]
        )

    @bentoml.api(input_spec=InferenceRequest, output_spec=InferenceResponse)
    def detect(self, **params: Any) -> InferenceResponse:
        request = InferenceRequest(**params)
        try:
            result = self.detect_pii.execute(request.model_id, request.text)
        except ModelNotAvailableError as exc:
            raise ModelNotFoundTransportError(str(exc)) from exc
        return to_inference_response(result)
