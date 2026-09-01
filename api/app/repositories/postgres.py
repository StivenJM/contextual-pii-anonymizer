from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.configuration import (
    DetectionSettings,
    Gazetteer,
    GazetteerEntry,
    ModelMapping,
    PatternRecognizer,
    ProtectionAction,
    ProtectionRule,
)
from app.domain.detections import DetectionSource
from app.infrastructure.models import (
    DetectionSettingsModel,
    GazetteerEntryModel,
    GazetteerModel,
    ModelMappingModel,
    PatternRecognizerModel,
    ProtectionRuleModel,
    SystemSettingModel,
)


class PostgresConfigurationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_active_model_id(self) -> str | None:
        setting = await self._session.get(SystemSettingModel, 1)
        return setting.active_model_id if setting else None

    async def set_active_model_id(self, model_id: str) -> None:
        setting = await self._session.get(SystemSettingModel, 1)
        if setting is None:
            setting = SystemSettingModel(id=1, active_model_id=model_id)
            self._session.add(setting)
        else:
            setting.active_model_id = model_id

    async def list_mappings(self, model_id: str) -> list[ModelMapping]:
        rows = (
            await self._session.scalars(
                select(ModelMappingModel)
                .where(ModelMappingModel.model_id == model_id)
                .order_by(ModelMappingModel.native_entity_type)
            )
        ).all()
        return [self._mapping(row) for row in rows]

    async def get_mapping(self, mapping_id: int) -> ModelMapping | None:
        row = await self._session.get(ModelMappingModel, mapping_id)
        return self._mapping(row) if row else None

    async def create_mapping(self, mapping: ModelMapping) -> ModelMapping:
        row = ModelMappingModel(
            model_id=mapping.model_id,
            native_entity_type=mapping.native_entity_type,
            canonical_type=mapping.canonical_type,
        )
        self._session.add(row)
        await self._session.flush()
        return self._mapping(row)

    async def update_mapping(self, mapping: ModelMapping) -> ModelMapping:
        row = await self._session.get(ModelMappingModel, mapping.id)
        if row is None:
            raise LookupError("Mapping not found")
        row.model_id = mapping.model_id
        row.native_entity_type = mapping.native_entity_type
        row.canonical_type = mapping.canonical_type
        await self._session.flush()
        return self._mapping(row)

    async def delete_mapping(self, mapping_id: int) -> bool:
        result = await self._session.execute(
            delete(ModelMappingModel).where(ModelMappingModel.id == mapping_id)
        )
        return bool(result.rowcount)

    async def list_patterns(self) -> list[PatternRecognizer]:
        rows = (
            await self._session.scalars(
                select(PatternRecognizerModel).order_by(PatternRecognizerModel.id)
            )
        ).all()
        return [self._pattern(row) for row in rows]

    async def get_pattern(self, recognizer_id: int) -> PatternRecognizer | None:
        row = await self._session.get(PatternRecognizerModel, recognizer_id)
        return self._pattern(row) if row else None

    async def save_pattern(self, recognizer: PatternRecognizer) -> PatternRecognizer:
        row = await self._session.get(PatternRecognizerModel, recognizer.id) if recognizer.id else None
        if row is None:
            row = PatternRecognizerModel()
            self._session.add(row)
        row.name = recognizer.name
        row.canonical_type = recognizer.canonical_type
        row.patterns = list(recognizer.patterns)
        row.score = recognizer.score
        row.context_words = list(recognizer.context_words)
        row.validator = recognizer.validator
        row.enabled = recognizer.enabled
        await self._session.flush()
        return self._pattern(row)

    async def delete_pattern(self, recognizer_id: int) -> bool:
        result = await self._session.execute(
            delete(PatternRecognizerModel).where(PatternRecognizerModel.id == recognizer_id)
        )
        return bool(result.rowcount)

    async def list_gazetteers(self) -> list[Gazetteer]:
        rows = (
            await self._session.scalars(select(GazetteerModel).order_by(GazetteerModel.id))
        ).all()
        return [self._gazetteer(row) for row in rows]

    async def get_gazetteer(self, gazetteer_id: int) -> Gazetteer | None:
        row = await self._session.get(GazetteerModel, gazetteer_id)
        return self._gazetteer(row) if row else None

    async def save_gazetteer(self, gazetteer: Gazetteer) -> Gazetteer:
        row = await self._session.get(GazetteerModel, gazetteer.id) if gazetteer.id else None
        if row is None:
            row = GazetteerModel(entries=[])
            self._session.add(row)
        row.name = gazetteer.name
        row.canonical_type = gazetteer.canonical_type
        row.score = gazetteer.score
        row.case_sensitive = gazetteer.case_sensitive
        row.enabled = gazetteer.enabled
        await self._session.flush()
        return self._gazetteer(row)

    async def delete_gazetteer(self, gazetteer_id: int) -> bool:
        result = await self._session.execute(
            delete(GazetteerModel).where(GazetteerModel.id == gazetteer_id)
        )
        return bool(result.rowcount)

    async def save_gazetteer_entry(
        self,
        gazetteer_id: int,
        entry: GazetteerEntry,
    ) -> GazetteerEntry:
        row = await self._session.get(GazetteerEntryModel, entry.id) if entry.id else None
        if row is None:
            row = GazetteerEntryModel(gazetteer_id=gazetteer_id)
            self._session.add(row)
        elif row.gazetteer_id != gazetteer_id:
            raise LookupError("Gazetteer entry not found")
        row.value = entry.value
        await self._session.flush()
        return GazetteerEntry(id=row.id, value=row.value)

    async def delete_gazetteer_entry(self, entry_id: int) -> bool:
        result = await self._session.execute(
            delete(GazetteerEntryModel).where(GazetteerEntryModel.id == entry_id)
        )
        return bool(result.rowcount)

    async def get_detection_settings(self) -> DetectionSettings:
        row = await self._session.get(DetectionSettingsModel, 1)
        if row is None:
            return DetectionSettings()
        return DetectionSettings(
            threshold=row.threshold,
            model_enabled=row.model_enabled,
            pattern_enabled=row.pattern_enabled,
            gazetteer_enabled=row.gazetteer_enabled,
            source_priority=tuple(DetectionSource(value) for value in row.source_priority),
        )

    async def save_detection_settings(self, settings: DetectionSettings) -> DetectionSettings:
        row = await self._session.get(DetectionSettingsModel, 1)
        if row is None:
            row = DetectionSettingsModel(id=1)
            self._session.add(row)
        row.threshold = settings.threshold
        row.model_enabled = settings.model_enabled
        row.pattern_enabled = settings.pattern_enabled
        row.gazetteer_enabled = settings.gazetteer_enabled
        row.source_priority = [source.value for source in settings.source_priority]
        await self._session.flush()
        return settings

    async def list_protection_rules(self) -> list[ProtectionRule]:
        rows = (
            await self._session.scalars(
                select(ProtectionRuleModel).order_by(ProtectionRuleModel.canonical_type)
            )
        ).all()
        return [self._rule(row) for row in rows]

    async def get_protection_rule(self, rule_id: int) -> ProtectionRule | None:
        row = await self._session.get(ProtectionRuleModel, rule_id)
        return self._rule(row) if row else None

    async def save_protection_rule(self, rule: ProtectionRule) -> ProtectionRule:
        row = await self._session.get(ProtectionRuleModel, rule.id) if rule.id else None
        if row is None:
            row = ProtectionRuleModel()
            self._session.add(row)
        row.canonical_type = rule.canonical_type
        row.action = rule.action.value
        await self._session.flush()
        return self._rule(row)

    async def delete_protection_rule(self, rule_id: int) -> bool:
        result = await self._session.execute(
            delete(ProtectionRuleModel).where(ProtectionRuleModel.id == rule_id)
        )
        return bool(result.rowcount)

    async def commit(self) -> None:
        await self._session.commit()

    @staticmethod
    def _mapping(row: ModelMappingModel) -> ModelMapping:
        return ModelMapping(row.id, row.model_id, row.native_entity_type, row.canonical_type)

    @staticmethod
    def _pattern(row: PatternRecognizerModel) -> PatternRecognizer:
        return PatternRecognizer(
            row.id,
            row.name,
            row.canonical_type,
            tuple(row.patterns),
            row.score,
            tuple(row.context_words),
            row.validator,
            row.enabled,
        )

    @staticmethod
    def _gazetteer(row: GazetteerModel) -> Gazetteer:
        return Gazetteer(
            row.id,
            row.name,
            row.canonical_type,
            row.score,
            row.case_sensitive,
            row.enabled,
            tuple(GazetteerEntry(item.id, item.value) for item in row.entries),
        )

    @staticmethod
    def _rule(row: ProtectionRuleModel) -> ProtectionRule:
        return ProtectionRule(row.id, row.canonical_type, ProtectionAction(row.action))
