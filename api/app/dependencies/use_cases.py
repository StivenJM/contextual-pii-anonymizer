from typing import Annotated

from fastapi import Depends

from app.dependencies.repositories import get_configuration_repository
from app.dependencies.services import get_inference_service
from app.repositories.configuration import ConfigurationRepository
from app.services.inference import InferenceService
from app.use_cases.administration import AdministrationUseCases
from app.use_cases.interactions import ProtectInteractionUseCase


def get_administration_use_cases(
    repository: Annotated[
        ConfigurationRepository,
        Depends(get_configuration_repository),
    ],
    inference: Annotated[InferenceService, Depends(get_inference_service)],
) -> AdministrationUseCases:
    return AdministrationUseCases(repository, inference)


def get_protect_interaction_use_case(
    repository: Annotated[
        ConfigurationRepository,
        Depends(get_configuration_repository),
    ],
    inference: Annotated[InferenceService, Depends(get_inference_service)],
) -> ProtectInteractionUseCase:
    return ProtectInteractionUseCase(repository, inference)
