from sqlalchemy import URL, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings


AsyncSessionFactory = async_sessionmaker[AsyncSession]


def create_database_url(settings: Settings) -> URL:
    return URL.create(
        drivername="postgresql+psycopg",
        username=settings.postgres_user,
        password=settings.postgres_password.get_secret_value(),
        host=settings.postgres_host,
        port=settings.postgres_port,
        database=settings.postgres_db,
    )


def create_database_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(create_database_url(settings))


def create_session_factory(engine: AsyncEngine) -> AsyncSessionFactory:
    return async_sessionmaker(bind=engine)


async def verify_database_connection(engine: AsyncEngine) -> None:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
