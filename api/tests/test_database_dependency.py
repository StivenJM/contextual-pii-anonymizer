import unittest

from app.container import AppContainer
from app.dependencies.database import get_database_session


class FakeSessionContext:
    def __init__(self, session: object) -> None:
        self.session = session
        self.closed = False

    async def __aenter__(self) -> object:
        return self.session

    async def __aexit__(self, *_args: object) -> None:
        self.closed = True


class FakeSessionFactory:
    def __init__(self) -> None:
        self.contexts: list[FakeSessionContext] = []

    def __call__(self) -> FakeSessionContext:
        context = FakeSessionContext(object())
        self.contexts.append(context)
        return context


class DatabaseDependencyTests(unittest.IsolatedAsyncioTestCase):
    async def test_creates_and_closes_one_session_per_request(self) -> None:
        factory = FakeSessionFactory()
        container = AppContainer(session_factory=factory)  # type: ignore[arg-type]

        first = await self._consume_session(container)
        second = await self._consume_session(container)

        self.assertIsNot(first, second)
        self.assertEqual(len(factory.contexts), 2)
        self.assertTrue(all(context.closed for context in factory.contexts))

    async def _consume_session(self, container: AppContainer) -> object:
        dependency = get_database_session(container)
        session = await anext(dependency)
        await dependency.aclose()
        return session


if __name__ == "__main__":
    unittest.main()
