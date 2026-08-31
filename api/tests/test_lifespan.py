import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI

from app.lifespan import lifespan


class LifespanTests(unittest.IsolatedAsyncioTestCase):
    async def test_builds_container_after_check_and_disposes_engine(self) -> None:
        engine = MagicMock()
        engine.dispose = AsyncMock()
        session_factory = MagicMock()
        connection_check = AsyncMock()
        app = FastAPI()

        with (
            patch("app.lifespan.Settings"),
            patch("app.lifespan.create_database_engine", return_value=engine),
            patch(
                "app.lifespan.create_session_factory",
                return_value=session_factory,
            ),
            patch(
                "app.lifespan.verify_database_connection",
                new=connection_check,
            ),
        ):
            async with lifespan(app):
                self.assertIs(
                    app.state.container.session_factory,
                    session_factory,
                )
                connection_check.assert_awaited_once_with(engine)

        engine.dispose.assert_awaited_once_with()

    async def test_connection_failure_aborts_startup_and_disposes_engine(self) -> None:
        engine = MagicMock()
        engine.dispose = AsyncMock()
        connection_check = AsyncMock(side_effect=ConnectionError("unavailable"))
        app = FastAPI()

        with (
            patch("app.lifespan.Settings"),
            patch("app.lifespan.create_database_engine", return_value=engine),
            patch(
                "app.lifespan.verify_database_connection",
                new=connection_check,
            ),
        ):
            with self.assertRaises(ConnectionError):
                async with lifespan(app):
                    self.fail("Startup must not complete when PostgreSQL is unavailable.")

        engine.dispose.assert_awaited_once_with()


if __name__ == "__main__":
    unittest.main()
