from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.dependencies.use_cases import get_administration_use_cases
from app.domain.configuration import (
    DetectionSettings,
    Gazetteer,
    GazetteerEntry,
    ModelMapping,
    PatternRecognizer,
    ProtectionRule,
)
from app.schemas.administration import (
    ActiveModelRequest,
    DetectionSettingsRequest,
    DetectionSettingsResponse,
    EnabledRequest,
    GazetteerEntryRequest,
    GazetteerEntryResponse,
    GazetteerRequest,
    GazetteerResponse,
    MappingRequest,
    MappingResponse,
    MappingUpdateRequest,
    ModelMetadataResponse,
    PatternRequest,
    PatternResponse,
    ProtectionRuleRequest,
    ProtectionRuleResponse,
)
from app.use_cases.administration import AdministrationUseCases


router = APIRouter(prefix="/api/admin", tags=["administration"])
AdminDep = Annotated[AdministrationUseCases, Depends(get_administration_use_cases)]


@router.get("/taxonomy")
async def get_taxonomy(use_cases: AdminDep) -> dict[str, object]:
    return use_cases.get_taxonomy()


@router.get("/models", response_model=list[ModelMetadataResponse])
async def list_models(use_cases: AdminDep) -> list[ModelMetadataResponse]:
    return [ModelMetadataResponse.model_validate(item) for item in await use_cases.list_models()]


@router.get("/models/active", response_model=ModelMetadataResponse | None)
async def get_active_model(use_cases: AdminDep) -> ModelMetadataResponse | None:
    model = await use_cases.get_active_model()
    return ModelMetadataResponse.model_validate(model) if model else None


@router.put("/models/active", response_model=ModelMetadataResponse)
async def set_active_model(
    body: ActiveModelRequest,
    use_cases: AdminDep,
) -> ModelMetadataResponse:
    return ModelMetadataResponse.model_validate(
        await use_cases.set_active_model(body.model_id)
    )


@router.get("/models/{model_id}", response_model=ModelMetadataResponse)
async def get_model(model_id: str, use_cases: AdminDep) -> ModelMetadataResponse:
    return ModelMetadataResponse.model_validate(await use_cases.get_model(model_id))


@router.get("/models/{model_id}/mappings", response_model=list[MappingResponse])
async def list_mappings(model_id: str, use_cases: AdminDep) -> list[MappingResponse]:
    return [MappingResponse.model_validate(item) for item in await use_cases.list_mappings(model_id)]


@router.get("/models/{model_id}/mapping-gaps", response_model=list[str])
async def list_mapping_gaps(model_id: str, use_cases: AdminDep) -> list[str]:
    return await use_cases.mapping_gaps(model_id)


@router.post(
    "/models/{model_id}/mappings",
    response_model=MappingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_mapping(
    model_id: str,
    body: MappingRequest,
    use_cases: AdminDep,
) -> MappingResponse:
    item = await use_cases.create_mapping(
        ModelMapping(None, model_id, body.native_entity_type, body.canonical_type)
    )
    return MappingResponse.model_validate(item)


@router.put("/mappings/{mapping_id}", response_model=MappingResponse)
async def update_mapping(
    mapping_id: int,
    body: MappingUpdateRequest,
    use_cases: AdminDep,
) -> MappingResponse:
    item = await use_cases.update_mapping(
        ModelMapping(
            mapping_id,
            body.model_id,
            body.native_entity_type,
            body.canonical_type,
        )
    )
    return MappingResponse.model_validate(item)


@router.delete("/mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mapping(mapping_id: int, use_cases: AdminDep) -> Response:
    await use_cases.delete_mapping(mapping_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _pattern(body: PatternRequest, recognizer_id: int | None = None) -> PatternRecognizer:
    return PatternRecognizer(
        recognizer_id,
        body.name,
        body.canonical_type,
        tuple(body.patterns),
        body.score,
        tuple(body.context_words),
        body.validator,
        body.enabled,
    )


@router.get("/patterns", response_model=list[PatternResponse])
async def list_patterns(use_cases: AdminDep) -> list[PatternResponse]:
    return [PatternResponse.model_validate(item) for item in await use_cases.list_patterns()]


@router.get("/patterns/{recognizer_id}", response_model=PatternResponse)
async def get_pattern(recognizer_id: int, use_cases: AdminDep) -> PatternResponse:
    return PatternResponse.model_validate(await use_cases.get_pattern(recognizer_id))


@router.post("/patterns", response_model=PatternResponse, status_code=status.HTTP_201_CREATED)
async def create_pattern(body: PatternRequest, use_cases: AdminDep) -> PatternResponse:
    return PatternResponse.model_validate(await use_cases.save_pattern(_pattern(body)))


@router.put("/patterns/{recognizer_id}", response_model=PatternResponse)
async def update_pattern(
    recognizer_id: int,
    body: PatternRequest,
    use_cases: AdminDep,
) -> PatternResponse:
    await use_cases.get_pattern(recognizer_id)
    return PatternResponse.model_validate(
        await use_cases.save_pattern(_pattern(body, recognizer_id))
    )


@router.patch("/patterns/{recognizer_id}/enabled", response_model=PatternResponse)
async def set_pattern_enabled(
    recognizer_id: int,
    body: EnabledRequest,
    use_cases: AdminDep,
) -> PatternResponse:
    current = await use_cases.get_pattern(recognizer_id)
    updated = PatternRecognizer(
        current.id,
        current.name,
        current.canonical_type,
        current.patterns,
        current.score,
        current.context_words,
        current.validator,
        body.enabled,
    )
    return PatternResponse.model_validate(await use_cases.save_pattern(updated))


@router.delete("/patterns/{recognizer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pattern(recognizer_id: int, use_cases: AdminDep) -> Response:
    await use_cases.delete_pattern(recognizer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _gazetteer(body: GazetteerRequest, gazetteer_id: int | None = None) -> Gazetteer:
    return Gazetteer(
        gazetteer_id,
        body.name,
        body.canonical_type,
        body.score,
        body.case_sensitive,
        body.enabled,
    )


@router.get("/gazetteers", response_model=list[GazetteerResponse])
async def list_gazetteers(use_cases: AdminDep) -> list[GazetteerResponse]:
    return [GazetteerResponse.model_validate(item) for item in await use_cases.list_gazetteers()]


@router.get("/gazetteers/{gazetteer_id}", response_model=GazetteerResponse)
async def get_gazetteer(gazetteer_id: int, use_cases: AdminDep) -> GazetteerResponse:
    return GazetteerResponse.model_validate(await use_cases.get_gazetteer(gazetteer_id))


@router.post("/gazetteers", response_model=GazetteerResponse, status_code=status.HTTP_201_CREATED)
async def create_gazetteer(body: GazetteerRequest, use_cases: AdminDep) -> GazetteerResponse:
    return GazetteerResponse.model_validate(
        await use_cases.save_gazetteer(_gazetteer(body))
    )


@router.put("/gazetteers/{gazetteer_id}", response_model=GazetteerResponse)
async def update_gazetteer(
    gazetteer_id: int,
    body: GazetteerRequest,
    use_cases: AdminDep,
) -> GazetteerResponse:
    await use_cases.get_gazetteer(gazetteer_id)
    return GazetteerResponse.model_validate(
        await use_cases.save_gazetteer(_gazetteer(body, gazetteer_id))
    )


@router.patch("/gazetteers/{gazetteer_id}/enabled", response_model=GazetteerResponse)
async def set_gazetteer_enabled(
    gazetteer_id: int,
    body: EnabledRequest,
    use_cases: AdminDep,
) -> GazetteerResponse:
    current = await use_cases.get_gazetteer(gazetteer_id)
    updated = Gazetteer(
        current.id,
        current.name,
        current.canonical_type,
        current.score,
        current.case_sensitive,
        body.enabled,
        current.entries,
    )
    return GazetteerResponse.model_validate(await use_cases.save_gazetteer(updated))


@router.delete("/gazetteers/{gazetteer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gazetteer(gazetteer_id: int, use_cases: AdminDep) -> Response:
    await use_cases.delete_gazetteer(gazetteer_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/gazetteers/{gazetteer_id}/entries",
    response_model=list[GazetteerEntryResponse],
)
async def list_gazetteer_entries(
    gazetteer_id: int,
    use_cases: AdminDep,
) -> list[GazetteerEntryResponse]:
    gazetteer = await use_cases.get_gazetteer(gazetteer_id)
    return [GazetteerEntryResponse.model_validate(item) for item in gazetteer.entries]


@router.post(
    "/gazetteers/{gazetteer_id}/entries",
    response_model=GazetteerEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_gazetteer_entry(
    gazetteer_id: int,
    body: GazetteerEntryRequest,
    use_cases: AdminDep,
) -> GazetteerEntryResponse:
    item = await use_cases.save_gazetteer_entry(
        gazetteer_id,
        GazetteerEntry(None, body.value),
    )
    return GazetteerEntryResponse.model_validate(item)


@router.put(
    "/gazetteers/{gazetteer_id}/entries/{entry_id}",
    response_model=GazetteerEntryResponse,
)
async def update_gazetteer_entry(
    gazetteer_id: int,
    entry_id: int,
    body: GazetteerEntryRequest,
    use_cases: AdminDep,
) -> GazetteerEntryResponse:
    item = await use_cases.save_gazetteer_entry(
        gazetteer_id,
        GazetteerEntry(entry_id, body.value),
    )
    return GazetteerEntryResponse.model_validate(item)


@router.delete(
    "/gazetteers/{gazetteer_id}/entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_gazetteer_entry(
    gazetteer_id: int,
    entry_id: int,
    use_cases: AdminDep,
) -> Response:
    await use_cases.get_gazetteer(gazetteer_id)
    await use_cases.delete_gazetteer_entry(entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/detection-settings", response_model=DetectionSettingsResponse)
async def get_detection_settings(use_cases: AdminDep) -> DetectionSettingsResponse:
    return DetectionSettingsResponse.model_validate(
        await use_cases.get_detection_settings()
    )


@router.put("/detection-settings", response_model=DetectionSettingsResponse)
async def update_detection_settings(
    body: DetectionSettingsRequest,
    use_cases: AdminDep,
) -> DetectionSettingsResponse:
    settings = DetectionSettings(
        threshold=body.threshold,
        model_enabled=body.model_enabled,
        pattern_enabled=body.pattern_enabled,
        gazetteer_enabled=body.gazetteer_enabled,
        source_priority=tuple(body.source_priority),
    )
    return DetectionSettingsResponse.model_validate(
        await use_cases.save_detection_settings(settings)
    )


@router.get("/protection-rules", response_model=list[ProtectionRuleResponse])
async def list_protection_rules(use_cases: AdminDep) -> list[ProtectionRuleResponse]:
    return [
        ProtectionRuleResponse.model_validate(item)
        for item in await use_cases.list_protection_rules()
    ]


@router.get("/protection-rules/{rule_id}", response_model=ProtectionRuleResponse)
async def get_protection_rule(rule_id: int, use_cases: AdminDep) -> ProtectionRuleResponse:
    return ProtectionRuleResponse.model_validate(
        await use_cases.get_protection_rule(rule_id)
    )


@router.post(
    "/protection-rules",
    response_model=ProtectionRuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_protection_rule(
    body: ProtectionRuleRequest,
    use_cases: AdminDep,
) -> ProtectionRuleResponse:
    return ProtectionRuleResponse.model_validate(
        await use_cases.save_protection_rule(
            ProtectionRule(None, body.canonical_type, body.action)
        )
    )


@router.put("/protection-rules/{rule_id}", response_model=ProtectionRuleResponse)
async def update_protection_rule(
    rule_id: int,
    body: ProtectionRuleRequest,
    use_cases: AdminDep,
) -> ProtectionRuleResponse:
    await use_cases.get_protection_rule(rule_id)
    return ProtectionRuleResponse.model_validate(
        await use_cases.save_protection_rule(
            ProtectionRule(rule_id, body.canonical_type, body.action)
        )
    )


@router.delete("/protection-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_protection_rule(rule_id: int, use_cases: AdminDep) -> Response:
    await use_cases.delete_protection_rule(rule_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
