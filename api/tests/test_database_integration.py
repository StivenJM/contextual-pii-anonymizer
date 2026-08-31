import os
import unittest
from typing import Annotated

from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.database import get_database_session
from app.main import create_app
from app.runtime import create_selector_event_loop


@unittest.skipUnless(
    os.getenv("RUN_DATABASE_INTEGRATION") == "1",
    "Set RUN_DATABASE_INTEGRATION=1 to verify PostgreSQL integration.",
)
class DatabaseIntegrationTests(unittest.TestCase):
    def test_request_scoped_session_executes_against_postgresql(self) -> None:
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

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"value": 1})


if __name__ == "__main__":
    unittest.main()
