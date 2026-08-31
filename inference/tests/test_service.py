import unittest
from http import HTTPStatus
from typing import Any
from unittest.mock import patch

from starlette.testclient import TestClient

from app.entities.models import Detection, ModelMetadata
from app.service import (
    ModelNotFoundTransportError,
    PiiInferenceService,
    to_inference_response,
    to_metadata_response,
)
from app.use_cases.inference import InferenceResult


class FakeOpenMedModel:
    instances_created = 0

    def __init__(self) -> None:
        type(self).instances_created += 1
        self.received_texts: list[str] = []

    @property
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            id="fake-openmed",
            name="Fake OpenMed",
            version="test",
            description="Lightweight service test model.",
            native_entity_types=("PER",),
        )

    def detect(self, text: str) -> list[Detection]:
        self.received_texts.append(text)
        return [Detection("PER", text, 0, len(text), 0.98)]


class ServiceMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeOpenMedModel.instances_created = 0

    def test_bento_service_discovers_and_executes_registered_model(self) -> None:
        service = self._service()

        discovery = service.models()
        response = service.detect(model_id="fake-openmed", text="Juan")

        self.assertEqual(FakeOpenMedModel.instances_created, 1)
        self.assertEqual(discovery.models[0].id, "fake-openmed")
        self.assertEqual(discovery.models[0].native_entity_types, ["PER"])
        self.assertEqual(response.model_id, "fake-openmed")
        self.assertEqual(response.model_version, "test")
        self.assertEqual(response.detections[0].text, "Juan")

    def test_bento_service_reuses_model_between_requests(self) -> None:
        service = self._service()

        service.detect(model_id="fake-openmed", text="first")
        service.detect(model_id="fake-openmed", text="second")

        model = service.detect_pii.catalog.resolve("fake-openmed")
        self.assertEqual(FakeOpenMedModel.instances_created, 1)
        self.assertEqual(model.received_texts, ["first", "second"])

    def test_bento_service_translates_unknown_model_error(self) -> None:
        service = self._service()

        with self.assertRaises(ModelNotFoundTransportError) as context:
            service.detect(model_id="unknown", text="Juan")

        self.assertEqual(context.exception.error_code, HTTPStatus.NOT_FOUND)
        self.assertIn("unknown", str(context.exception))

    def test_unknown_model_returns_http_404(self) -> None:
        with patch("app.service.OpenMedModel", FakeOpenMedModel):
            app = PiiInferenceService.to_asgi()
            with TestClient(app) as client:
                with self.assertLogs(
                    "bentoml._internal.server.http_app",
                    level="ERROR",
                ):
                    response = client.post(
                        "/detect",
                        json={"model_id": "unknown", "text": "Juan"},
                    )

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertIn("unknown", response.text)

    def test_maps_application_results_to_transport_contracts(self) -> None:
        metadata = FakeOpenMedModel().metadata
        result = InferenceResult(
            model_id=metadata.id,
            model_version=metadata.version,
            detections=[Detection("PER", "Juan", 0, 4, 0.98)],
        )

        metadata_response = to_metadata_response(metadata)
        inference_response = to_inference_response(result)

        self.assertEqual(metadata_response.id, "fake-openmed")
        self.assertEqual(metadata_response.native_entity_types, ["PER"])
        self.assertEqual(
            inference_response.model_dump(),
            {
                "model_id": "fake-openmed",
                "model_version": "test",
                "detections": [
                    {
                        "native_type": "PER",
                        "text": "Juan",
                        "start": 0,
                        "end": 4,
                        "confidence": 0.98,
                    }
                ],
            },
        )

    def _service(self) -> Any:
        with patch("app.service.OpenMedModel", FakeOpenMedModel):
            return PiiInferenceService.inner()


if __name__ == "__main__":
    unittest.main()
