from typing import Annotated

from fastapi import Depends

from app.container import AppContainer
from app.dependencies.database import get_container
from app.errors import InvalidConfigurationError
from app.services.inference import InferenceService


def get_inference_service(
    container: Annotated[AppContainer, Depends(get_container)],
) -> InferenceService:
    if container.inference_service is None:
        raise InvalidConfigurationError("Inference service is not configured.")
    return container.inference_service
