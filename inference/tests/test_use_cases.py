import unittest

from app.entities.models import Detection, ModelMetadata
from app.model_catalog import ModelCatalog, ModelNotAvailableError
from app.use_cases.inference import DetectPiiUseCase, DiscoverModelsUseCase


class FakePiiModel:
    def __init__(
        self,
        model_id: str,
        native_type: str,
        detections: list[Detection] | None = None,
    ) -> None:
        self._metadata = ModelMetadata(
            id=model_id,
            name=f"Model {model_id}",
            version="1",
            description="Test model.",
            native_entity_types=(native_type,),
        )
        self.detections = detections or []
        self.received_texts: list[str] = []

    @property
    def metadata(self) -> ModelMetadata:
        return self._metadata

    def detect(self, text: str) -> list[Detection]:
        self.received_texts.append(text)
        return self.detections


class InferenceUseCaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model_a = FakePiiModel(
            "fake-model-a",
            "NATIVE_A",
            [Detection("NATIVE_A", "Juan", 0, 4, 0.98)],
        )
        self.model_b = FakePiiModel(
            "fake-model-b",
            "NATIVE_B",
            [Detection("NATIVE_B", "Juan", 0, 4, 0.91)],
        )
        catalog = ModelCatalog([self.model_a, self.model_b])
        self.detect = DetectPiiUseCase(catalog)
        self.discover = DiscoverModelsUseCase(catalog)

    def test_discovers_metadata_without_transport_or_framework(self) -> None:
        metadata = self.discover.execute()

        self.assertEqual(
            [model.id for model in metadata],
            ["fake-model-a", "fake-model-b"],
        )
        self.assertEqual(metadata[0].name, "Model fake-model-a")
        self.assertEqual(metadata[0].version, "1")
        self.assertEqual(metadata[0].native_entity_types, ("NATIVE_A",))

    def test_selects_only_the_requested_model(self) -> None:
        result_a = self.detect.execute("fake-model-a", "first")
        result_b = self.detect.execute("fake-model-b", "second")

        self.assertEqual(result_a.model_id, "fake-model-a")
        self.assertEqual(result_a.model_version, "1")
        self.assertEqual(result_a.detections[0].native_type, "NATIVE_A")
        self.assertEqual(result_b.model_id, "fake-model-b")
        self.assertEqual(result_b.model_version, "1")
        self.assertEqual(result_b.detections[0].native_type, "NATIVE_B")
        self.assertEqual(self.model_a.received_texts, ["first"])
        self.assertEqual(self.model_b.received_texts, ["second"])

    def test_unknown_model_fails_without_executing_another_model(self) -> None:
        with self.assertRaises(ModelNotAvailableError) as context:
            self.detect.execute("unknown", "Juan")

        self.assertEqual(context.exception.model_id, "unknown")
        self.assertEqual(self.model_a.received_texts, [])
        self.assertEqual(self.model_b.received_texts, [])

    def test_preserves_native_labels_and_overlapping_detections(self) -> None:
        overlaps = [
            Detection("NATIVE_A", "Juan", 0, 4, 0.98),
            Detection("OTHER_NATIVE", "Juan", 0, 4, 0.75),
        ]
        model = FakePiiModel("overlap-model", "NATIVE_A", overlaps)
        use_case = DetectPiiUseCase(ModelCatalog([model]))

        result = use_case.execute("overlap-model", "Juan")

        self.assertEqual(result.detections, overlaps)

    def test_does_not_add_non_ml_detections(self) -> None:
        model = FakePiiModel("empty-model", "NATIVE", [])
        use_case = DetectPiiUseCase(ModelCatalog([model]))

        result = use_case.execute(
            "empty-model",
            "correo a@example.com, telefono 5551234, cedula 123456",
        )

        self.assertEqual(result.detections, [])

    def test_reuses_the_registered_model_instance(self) -> None:
        self.detect.execute("fake-model-a", "first")
        self.detect.execute("fake-model-a", "second")

        self.assertEqual(self.model_a.received_texts, ["first", "second"])


if __name__ == "__main__":
    unittest.main()
