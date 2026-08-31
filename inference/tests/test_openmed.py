import unittest

from app.services.implementations.openmed import MODEL_ID, OpenMedModel


class OpenMedModelTests(unittest.TestCase):
    def test_adapts_native_model_detections(self) -> None:
        text = "Juan vive en Quito"
        model = self._model_returning(
            [
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
        )

        detections = model.detect(text)

        self.assertEqual(model.model_id, MODEL_ID)
        self.assertEqual(
            [detection.__dict__ for detection in detections],
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

    def test_preserves_overlapping_detections(self) -> None:
        model = self._model_returning(
            [
                self._raw_detection(entity_group="PER", score=0.9),
                self._raw_detection(entity_group="LOC", score=0.8),
            ]
        )

        detections = model.detect("Juan")

        self.assertEqual(
            [detection.native_type for detection in detections],
            ["PER", "LOC"],
        )

    def test_normalizes_only_bio_prefixes(self) -> None:
        for label, expected in (("B-PER", "PER"), ("I-PER", "PER"), ("PER", "PER")):
            with self.subTest(label=label):
                raw = self._raw_detection(entity=label)
                raw.pop("entity_group")
                model = self._model_returning([raw])

                detection = model.detect("Juan")[0]

                self.assertEqual(detection.native_type, expected)

    def test_preserves_entity_group_exactly(self) -> None:
        model = self._model_returning(
            [self._raw_detection(entity_group="NativeLabel")]
        )

        detection = model.detect("Juan")[0]

        self.assertEqual(detection.native_type, "NativeLabel")

    def test_rejects_invalid_model_output(self) -> None:
        invalid_outputs = [
            self._raw_detection(start=-1),
            self._raw_detection(start=3, end=2),
            self._raw_detection(end=5),
            self._raw_detection(score=1.1),
        ]

        for raw in invalid_outputs:
            with self.subTest(raw=raw):
                model = self._model_returning([raw])

                with self.assertRaises(ValueError):
                    model.detect("Juan")

    def _model_returning(
        self,
        detections: list[dict[str, object]],
    ) -> OpenMedModel:
        return OpenMedModel(pipeline=lambda _: detections)

    def _raw_detection(self, **overrides: object) -> dict[str, object]:
        detection: dict[str, object] = {
            "entity_group": "PER",
            "entity": "B-PER",
            "score": 0.9,
            "word": "Juan",
            "start": 0,
            "end": 4,
        }
        detection.update(overrides)
        return detection


if __name__ == "__main__":
    unittest.main()
