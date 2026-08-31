import unittest

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.infrastructure.database import (
    create_database_engine,
    create_database_url,
    create_session_factory,
)


class DatabaseInfrastructureTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.password = "p@ss:/#word"
        self.settings = Settings(
            POSTGRES_HOST="127.0.0.1",
            POSTGRES_PORT=5432,
            POSTGRES_DB="contextual_pii",
            POSTGRES_USER="contextual_pii",
            POSTGRES_PASSWORD=self.password,
        )

    def test_builds_typed_url_without_leaking_or_corrupting_password(self) -> None:
        url = create_database_url(self.settings)

        self.assertEqual(url.drivername, "postgresql+psycopg")
        self.assertEqual(url.password, self.password)
        self.assertNotIn(self.password, str(url))

    async def test_session_factory_produces_distinct_async_sessions(self) -> None:
        engine = create_database_engine(self.settings)
        session_factory = create_session_factory(engine)
        first = session_factory()
        second = session_factory()

        try:
            self.assertIsInstance(first, AsyncSession)
            self.assertIsInstance(second, AsyncSession)
            self.assertIsNot(first, second)
            self.assertIs(first.bind, engine)
            self.assertIs(second.bind, engine)
        finally:
            await first.close()
            await second.close()
            await engine.dispose()


if __name__ == "__main__":
    unittest.main()
