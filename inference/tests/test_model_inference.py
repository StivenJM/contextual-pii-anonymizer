import unittest

from pydantic import ValidationError

from controllers.dtos.inference_dto import InferenceRequest
from models.openmed import MODEL_ID, OpenMedModel
from use_cases.model_inference import ModelInference


class ModelInferenceTests(unittest.TestCase):
    def test_returns_native_model_detections(self) -> None:
        text = "Juan vive en Quito"
        raw_detections = [
            {
                "entity_group": "PER",
                "score": 0.98765,
                "word": "Juan",
                "start": 0,
                "end": 4,
            },
            {
                "entity_group": "LOC",
                "score": 0.87654,
                "word": "Quito",
                "start": 13,
                "end": 18,
            },
        ]
        inference = self._inference_returning(raw_detections)

        response = inference.detect(InferenceRequest(text=text))

        self.assertEqual(response.model_id, MODEL_ID)
        self.assertEqual(
            [detection.model_dump() for detection in response.detections],
            [
                {
                    "native_type": "PER",
                    "text": "Juan",
                    "start": 0,
                    "end": 4,
                    "confidence": 0.98765,
                },
                {
                    "native_type": "LOC",
                    "text": "Quito",
                    "start": 13,
                    "end": 18,
                    "confidence": 0.87654,
                },
            ],
        )

    def test_does_not_detect_email_when_model_returns_nothing(self) -> None:
        inference = self._inference_returning([])

        response = inference.detect(InferenceRequest(text="usuario@example.com"))

        self.assertEqual(response.detections, [])

    def test_preserves_overlapping_model_detections_without_fusion(self) -> None:
        raw_detections = [
            {
                "entity_group": "PER",
                "score": 0.9,
                "word": "Juan",
                "start": 0,
                "end": 4,
            },
            {
                "entity_group": "LOC",
                "score": 0.8,
                "word": "Juan",
                "start": 0,
                "end": 4,
            },
        ]
        inference = self._inference_returning(raw_detections)

        response = inference.detect(InferenceRequest(text="Juan"))

        self.assertEqual(
            [detection.native_type for detection in response.detections],
            ["PER", "LOC"],
        )

    def test_removes_only_bio_prefix_from_technical_label(self) -> None:
        raw_detections = [
            {
                "entity": "B-PER",
                "score": 0.9,
                "word": "Juan",
                "start": 0,
                "end": 4,
            }
        ]
        inference = self._inference_returning(raw_detections)

        response = inference.detect(InferenceRequest(text="Juan"))

        self.assertEqual(response.detections[0].native_type, "PER")

    def test_preserves_entity_group_exactly_as_returned(self) -> None:
        raw_detections = [
            {
                "entity_group": "NativeLabel",
                "score": 0.9,
                "word": "Juan",
                "start": 0,
                "end": 4,
            }
        ]
        inference = self._inference_returning(raw_detections)

        response = inference.detect(InferenceRequest(text="Juan"))

        self.assertEqual(response.detections[0].native_type, "NativeLabel")

    def test_rejects_empty_and_whitespace_only_text(self) -> None:
        for text in ("", "   "):
            with self.subTest(text=text):
                with self.assertRaises(ValidationError):
                    InferenceRequest(text=text)

    def test_rejects_non_string_text(self) -> None:
        with self.assertRaises(ValidationError):
            InferenceRequest(text=123)  # type: ignore[arg-type]

    def _inference_returning(
        self,
        raw_detections: list[dict[str, object]],
    ) -> ModelInference:
        model = OpenMedModel(pipeline=lambda _: raw_detections)
        return ModelInference(model=model)


if __name__ == "__main__":
    unittest.main()
