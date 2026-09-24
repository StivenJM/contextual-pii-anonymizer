import os
from typing import Annotated

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_database_session
from app.main import create_app
from app.runtime import create_selector_event_loop

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_DATABASE_INTEGRATION") != "1",
        reason="Set RUN_DATABASE_INTEGRATION=1 to verify PostgreSQL integration.",
    ),
]


def test_request_scoped_session_executes_against_postgresql() -> None:
    app = create_app()

    @app.get("/_integration/database")
    async def check_database(
        session: Annotated[AsyncSession, Depends(get_database_session)],
    ) -> dict[str, int]:
        result = await session.execute(text("SELECT 1"))
        return {"value": result.scalar_one()}

    with TestClient(
        app,
        backend_options={"loop_factory": create_selector_event_loop},
    ) as client:
        response = client.get("/_integration/database")

    assert response.status_code == 200
    assert response.json() == {"value": 1}
