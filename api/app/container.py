from dataclasses import dataclass

from app.infrastructure.database import AsyncSessionFactory


@dataclass(frozen=True)
class AppContainer:
    session_factory: AsyncSessionFactory
