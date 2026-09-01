import unittest

from app.domain.configuration import ModelMapping
from app.errors import InvalidConfigurationError
from app.services.inference import ModelMetadata
from app.use_cases.administration import AdministrationUseCases


class MappingRepository:
    def __init__(self) -> None:
        self.mappings: list[ModelMapping] = []
        self.commits = 0

    async def list_mappings(self, model_id: str) -> list[ModelMapping]:
        return [item for item in self.mappings if item.model_id == model_id]

    async def create_mapping(self, mapping: ModelMapping) -> ModelMapping:
        created = ModelMapping(len(self.mappings) + 1, mapping.model_id, mapping.native_entity_type, mapping.canonical_type)
        self.mappings.append(created)
        return created

    async def commit(self) -> None:
        self.commits += 1


class MetadataInferenceService:
    async def get_model(self, model_id: str) -> ModelMetadata:
        return ModelMetadata(model_id, "Model", "v1", "test", ("EMAIL", "ORGANIZATION"))


class AdministrationUseCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_creates_valid_mapping_and_reports_unmapped_labels(self) -> None:
        repository = MappingRepository()
        use_cases = AdministrationUseCases(repository, MetadataInferenceService())
        mapping = await use_cases.create_mapping(ModelMapping(None, "model-a", "EMAIL", "EMAIL"))
        self.assertEqual(mapping.id, 1)
        self.assertEqual(await use_cases.mapping_gaps("model-a"), ["ORGANIZATION"])
        self.assertEqual(repository.commits, 1)

    async def test_rejects_invalid_canonical_and_native_types(self) -> None:
        use_cases = AdministrationUseCases(MappingRepository(), MetadataInferenceService())
        with self.assertRaises(ValueError):
            await use_cases.create_mapping(ModelMapping(None, "model-a", "EMAIL", "OTHER"))
        with self.assertRaises(InvalidConfigurationError):
            await use_cases.create_mapping(ModelMapping(None, "model-a", "CITY", "LOCATION"))


if __name__ == "__main__":
    unittest.main()
