from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
import httpx

from app.config import Settings
from app.container import AppContainer
from app.infrastructure.database import (
    create_database_engine,
    create_session_factory,
    verify_database_connection,
)
from app.services.http_inference import HttpInferenceService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    engine = create_database_engine(settings)

    try:
        await verify_database_connection(engine)
        async with httpx.AsyncClient(
            base_url=settings.bentoml_url,
            timeout=settings.bentoml_timeout_seconds,
        ) as inference_client:
            app.state.container = AppContainer(
                session_factory=create_session_factory(engine),
                inference_service=HttpInferenceService(inference_client),
            )
            yield
    finally:
        await engine.dispose()
