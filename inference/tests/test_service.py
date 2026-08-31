import unittest
from unittest.mock import patch

from app.entities.detections import Detection
from app.service import PiiInferenceService, to_response
from app.use_cases.inference import InferenceResult


class FakeOpenMedModel:
    model_id = "fake-openmed"

    def detect(self, text: str) -> list[Detection]:
        return [
            Detection(
                native_type="PER",
                text=text,
                start=0,
                end=len(text),
                confidence=0.98,
            )
        ]


class ServiceMappingTests(unittest.TestCase):
    def test_bento_service_composes_and_executes_the_use_case(self) -> None:
        with patch("app.service.OpenMedModel", FakeOpenMedModel):
            service = PiiInferenceService.inner()

        response = service.detect(text="Juan")

        self.assertEqual(response.model_id, "fake-openmed")
        self.assertEqual(response.detections[0].text, "Juan")

    def test_maps_application_result_to_transport_response(self) -> None:
        result = InferenceResult(
            model_id="model-id",
            detections=[
                Detection(
                    native_type="PER",
                    text="Juan",
                    start=0,
                    end=4,
                    confidence=0.98,
                )
            ],
        )

        response = to_response(result)

        self.assertEqual(
            response.model_dump(),
            {
                "model_id": "model-id",
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


if __name__ == "__main__":
    unittest.main()
