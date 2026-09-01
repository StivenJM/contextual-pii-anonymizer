from dataclasses import dataclass

from app.infrastructure.database import AsyncSessionFactory
from app.services.inference import InferenceService


@dataclass(frozen=True)
class AppContainer:
    session_factory: AsyncSessionFactory
    inference_service: InferenceService | None = None
