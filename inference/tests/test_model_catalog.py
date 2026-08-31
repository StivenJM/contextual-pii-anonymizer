import unittest

from app.entities.models import Detection, ModelMetadata
from app.model_catalog import ModelCatalog, ModelNotAvailableError


class StubModel:
    def __init__(self, model_id: str) -> None:
        self._metadata = ModelMetadata(
            id=model_id,
            name=model_id,
            version="1",
            description="Stub model.",
            native_entity_types=("NATIVE",),
        )

    @property
    def metadata(self) -> ModelMetadata:
        return self._metadata

    def detect(self, text: str) -> list[Detection]:
        return []


class ModelCatalogTests(unittest.TestCase):
    def test_lists_and_resolves_multiple_models_by_logical_id(self) -> None:
        model_b = StubModel("model-b")
        model_a = StubModel("model-a")
        catalog = ModelCatalog([model_b, model_a])

        self.assertEqual(
            [metadata.id for metadata in catalog.list_models()],
            ["model-a", "model-b"],
        )
        self.assertIs(catalog.resolve("model-a"), model_a)
        self.assertEqual(catalog.get_metadata("model-b"), model_b.metadata)

    def test_rejects_duplicate_logical_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate model id"):
            ModelCatalog([StubModel("same"), StubModel("same")])

    def test_unknown_model_has_an_explicit_application_error(self) -> None:
        catalog = ModelCatalog([StubModel("known")])

        with self.assertRaises(ModelNotAvailableError):
            catalog.resolve("unknown")


if __name__ == "__main__":
    unittest.main()
