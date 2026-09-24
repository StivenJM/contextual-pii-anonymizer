import pytest

from app.container import AppContainer
from app.dependencies.database import get_database_session

pytestmark = pytest.mark.anyio


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


async def consume_session(container: AppContainer) -> object:
    dependency = get_database_session(container)
    session = await anext(dependency)
    await dependency.aclose()
    return session


async def test_creates_and_closes_one_session_per_request() -> None:
    factory = FakeSessionFactory()
    container = AppContainer(session_factory=factory)  # type: ignore[arg-type]

    first = await consume_session(container)
    second = await consume_session(container)

    assert first is not second
    assert len(factory.contexts) == 2
    assert all(context.closed for context in factory.contexts)
