import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.infrastructure.database import (
    create_database_engine,
    create_database_url,
    create_session_factory,
)


@pytest.fixture
def database_settings() -> Settings:
    return Settings(
        POSTGRES_HOST="127.0.0.1",
        POSTGRES_PORT=5432,
        POSTGRES_DB="contextual_pii",
        POSTGRES_USER="contextual_pii",
        POSTGRES_PASSWORD="p@ss:/#word",
    )


def test_builds_typed_url_without_leaking_or_corrupting_password(
    database_settings: Settings,
) -> None:
    url = create_database_url(database_settings)

    assert url.drivername == "postgresql+psycopg"
    assert url.password == "p@ss:/#word"
    assert "p@ss:/#word" not in str(url)


@pytest.mark.anyio
async def test_session_factory_produces_distinct_async_sessions(
    database_settings: Settings,
) -> None:
    engine = create_database_engine(database_settings)
    session_factory = create_session_factory(engine)
    first = session_factory()
    second = session_factory()

    try:
        assert isinstance(first, AsyncSession)
        assert isinstance(second, AsyncSession)
        assert first is not second
        assert first.bind is engine
        assert second.bind is engine
    finally:
        await first.close()
        await second.close()
        await engine.dispose()
