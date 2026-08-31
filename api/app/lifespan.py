from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.container import AppContainer
from app.infrastructure.database import (
    create_database_engine,
    create_session_factory,
    verify_database_connection,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()
    engine = create_database_engine(settings)

    try:
        await verify_database_connection(engine)
        app.state.container = AppContainer(
            session_factory=create_session_factory(engine),
        )
        yield
    finally:
        await engine.dispose()
