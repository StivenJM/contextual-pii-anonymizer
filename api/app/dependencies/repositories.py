from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_database_session
from app.repositories.configuration import ConfigurationRepository
from app.repositories.postgres import PostgresConfigurationRepository


def get_configuration_repository(
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> ConfigurationRepository:
    return PostgresConfigurationRepository(session)
