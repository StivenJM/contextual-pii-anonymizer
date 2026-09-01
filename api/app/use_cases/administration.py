import re

from app.domain.configuration import (
    DetectionSettings,
    Gazetteer,
    GazetteerEntry,
    ModelMapping,
    PatternRecognizer,
    ProtectionRule,
)
from app.domain.detections import DetectionSource
from app.domain.taxonomy import get_node, taxonomy_tree
from app.engines.validators import VALIDATORS
from app.errors import InvalidConfigurationError, ResourceNotFoundError
from app.repositories.configuration import ConfigurationRepository
from app.services.inference import InferenceService, ModelMetadata


class AdministrationUseCases:
    def __init__(
        self,
        repository: ConfigurationRepository,
        inference: InferenceService,
    ):
        self._repository = repository
        self._inference = inference

    def get_taxonomy(self) -> dict[str, object]:
        return taxonomy_tree()

    async def list_models(self) -> list[ModelMetadata]:
        return await self._inference.list_models()

    async def get_model(self, model_id: str) -> ModelMetadata:
        return await self._inference.get_model(model_id)

    async def get_active_model(self) -> ModelMetadata | None:
        model_id = await self._repository.get_active_model_id()
        return await self._inference.get_model(model_id) if model_id else None

    async def set_active_model(self, model_id: str) -> ModelMetadata:
        model = await self._inference.get_model(model_id)
        await self._repository.set_active_model_id(model_id)
        await self._repository.commit()
        return model

    async def list_mappings(self, model_id: str) -> list[ModelMapping]:
        return await self._repository.list_mappings(model_id)

    async def mapping_gaps(self, model_id: str) -> list[str]:
        model = await self._inference.get_model(model_id)
        mapped = {
            item.native_entity_type
            for item in await self._repository.list_mappings(model_id)
        }
        return sorted(set(model.native_entity_types) - mapped)

    async def create_mapping(self, mapping: ModelMapping) -> ModelMapping:
        await self._validate_mapping(mapping)
        created = await self._repository.create_mapping(mapping)
        await self._repository.commit()
        return created

    async def update_mapping(self, mapping: ModelMapping) -> ModelMapping:
        if mapping.id is None or await self._repository.get_mapping(mapping.id) is None:
            raise ResourceNotFoundError("Mapping not found.")
        await self._validate_mapping(mapping)
        updated = await self._repository.update_mapping(mapping)
        await self._repository.commit()
        return updated

    async def delete_mapping(self, mapping_id: int) -> None:
        if not await self._repository.delete_mapping(mapping_id):
            raise ResourceNotFoundError("Mapping not found.")
        await self._repository.commit()

    async def _validate_mapping(self, mapping: ModelMapping) -> None:
        get_node(mapping.canonical_type)
        model = await self._inference.get_model(mapping.model_id)
        if mapping.native_entity_type not in model.native_entity_types:
            raise InvalidConfigurationError(
                f"Native entity type '{mapping.native_entity_type}' is not declared by model '{mapping.model_id}'."
            )

    async def list_patterns(self) -> list[PatternRecognizer]:
        return await self._repository.list_patterns()

    async def get_pattern(self, recognizer_id: int) -> PatternRecognizer:
        item = await self._repository.get_pattern(recognizer_id)
        if item is None:
            raise ResourceNotFoundError("Pattern recognizer not found.")
        return item

    async def save_pattern(self, recognizer: PatternRecognizer) -> PatternRecognizer:
        get_node(recognizer.canonical_type)
        if not recognizer.patterns:
            raise InvalidConfigurationError("At least one pattern is required.")
        try:
            for pattern in recognizer.patterns:
                re.compile(pattern)
        except re.error as exc:
            raise InvalidConfigurationError(f"Invalid regular expression: {exc}") from exc
        if recognizer.validator and recognizer.validator not in VALIDATORS:
            raise InvalidConfigurationError(f"Unknown validator: {recognizer.validator}")
        saved = await self._repository.save_pattern(recognizer)
        await self._repository.commit()
        return saved

    async def delete_pattern(self, recognizer_id: int) -> None:
        if not await self._repository.delete_pattern(recognizer_id):
            raise ResourceNotFoundError("Pattern recognizer not found.")
        await self._repository.commit()

    async def list_gazetteers(self) -> list[Gazetteer]:
        return await self._repository.list_gazetteers()

    async def get_gazetteer(self, gazetteer_id: int) -> Gazetteer:
        item = await self._repository.get_gazetteer(gazetteer_id)
        if item is None:
            raise ResourceNotFoundError("Gazetteer not found.")
        return item

    async def save_gazetteer(self, gazetteer: Gazetteer) -> Gazetteer:
        get_node(gazetteer.canonical_type)
        saved = await self._repository.save_gazetteer(gazetteer)
        await self._repository.commit()
        return saved

    async def delete_gazetteer(self, gazetteer_id: int) -> None:
        if not await self._repository.delete_gazetteer(gazetteer_id):
            raise ResourceNotFoundError("Gazetteer not found.")
        await self._repository.commit()

    async def save_gazetteer_entry(
        self,
        gazetteer_id: int,
        entry: GazetteerEntry,
    ) -> GazetteerEntry:
        await self.get_gazetteer(gazetteer_id)
        if not entry.value.strip():
            raise InvalidConfigurationError("Gazetteer entry cannot be blank.")
        saved = await self._repository.save_gazetteer_entry(gazetteer_id, entry)
        await self._repository.commit()
        return saved

    async def delete_gazetteer_entry(self, entry_id: int) -> None:
        if not await self._repository.delete_gazetteer_entry(entry_id):
            raise ResourceNotFoundError("Gazetteer entry not found.")
        await self._repository.commit()

    async def get_detection_settings(self) -> DetectionSettings:
        return await self._repository.get_detection_settings()

    async def save_detection_settings(self, settings: DetectionSettings) -> DetectionSettings:
        if not 0 <= settings.threshold <= 1:
            raise InvalidConfigurationError("Threshold must be between 0 and 1.")
        if len(settings.source_priority) != len(set(settings.source_priority)):
            raise InvalidConfigurationError("Source priority cannot contain duplicates.")
        if set(settings.source_priority) != set(DetectionSource):
            raise InvalidConfigurationError("Source priority must include every detection source.")
        saved = await self._repository.save_detection_settings(settings)
        await self._repository.commit()
        return saved

    async def list_protection_rules(self) -> list[ProtectionRule]:
        return await self._repository.list_protection_rules()

    async def get_protection_rule(self, rule_id: int) -> ProtectionRule:
        item = await self._repository.get_protection_rule(rule_id)
        if item is None:
            raise ResourceNotFoundError("Protection rule not found.")
        return item

    async def save_protection_rule(self, rule: ProtectionRule) -> ProtectionRule:
        get_node(rule.canonical_type)
        saved = await self._repository.save_protection_rule(rule)
        await self._repository.commit()
        return saved

    async def delete_protection_rule(self, rule_id: int) -> None:
        if not await self._repository.delete_protection_rule(rule_id):
            raise ResourceNotFoundError("Protection rule not found.")
        await self._repository.commit()
