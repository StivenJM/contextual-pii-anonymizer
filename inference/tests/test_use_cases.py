import unittest

from app.entities.detections import Detection
from app.use_cases.inference import DetectPiiUseCase


class FakePiiModel:
    model_id = "fake-model"

    def __init__(self, detections: list[Detection]) -> None:
        self.detections = detections
        self.received_text: str | None = None

    def detect(self, text: str) -> list[Detection]:
        self.received_text = text
        return self.detections


class DetectPiiUseCaseTests(unittest.TestCase):
    def test_orchestrates_model_inference_without_transport_types(self) -> None:
        detections = [
            Detection(
                native_type="PER",
                text="Juan",
                start=0,
                end=4,
                confidence=0.98,
            )
        ]
        model = FakePiiModel(detections)
        use_case = DetectPiiUseCase(model=model)

        result = use_case.execute("Juan vive en Quito")

        self.assertEqual(model.received_text, "Juan vive en Quito")
        self.assertEqual(result.model_id, "fake-model")
        self.assertEqual(result.detections, detections)

    def test_does_not_add_rule_based_detections(self) -> None:
        use_case = DetectPiiUseCase(model=FakePiiModel([]))

        result = use_case.execute("usuario@example.com")

        self.assertEqual(result.detections, [])


if __name__ == "__main__":
    unittest.main()
