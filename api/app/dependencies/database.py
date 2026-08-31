from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.container import AppContainer


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


async def get_database_session(
    container: Annotated[AppContainer, Depends(get_container)],
) -> AsyncIterator[AsyncSession]:
    async with container.session_factory() as session:
        yield session
