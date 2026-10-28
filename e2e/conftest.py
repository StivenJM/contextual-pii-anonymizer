from __future__ import annotations

import os
import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
from playwright.sync_api import (
    BrowserContext,
    Page,
    Worker,
    sync_playwright,
)

from support.artifacts import recording
from support.extension import BUILD_DIRECTORY, BuildReport, build_patched_extension
from support.servers import (
    DEFAULT_MARKDOWN,
    DEFAULT_TOKEN,
    ConverterStub,
    MiddlewareStub,
    StaticSite,
    default_protect,
)

ASSETS = Path(__file__).resolve().parent / "assets"
BUILD_ROOT = BUILD_DIRECTORY.parent


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("e2e")
    group.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Show the Chromium window while the tests run.",
    )
    group.addoption(
        "--slowmo",
        type=int,
        default=0,
        metavar="MS",
        help="Slow browser operations down by MS milliseconds.",
    )
    group.addoption(
        "--pw-trace",
        choices=("off", "on", "retain-on-failure"),
        default="off",
        help="Record a Playwright trace per test and keep it per MODE.",
    )


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    report = yield
    if report.when == "call":
        item.rep_call = report
    return report


@dataclass(frozen=True)
class Harness:
    build: BuildReport
    context: BrowserContext
    worker: Worker
    extension_id: str


@pytest.fixture(scope="session")
def chat_site() -> str:
    site = StaticSite(ASSETS)
    url = site.start()
    try:
        yield url
    finally:
        site.stop()


@pytest.fixture(scope="session")
def converter() -> ConverterStub:
    stub = ConverterStub(DEFAULT_TOKEN)
    stub.start()
    try:
        yield stub
    finally:
        stub.stop()


@pytest.fixture(scope="session")
def middleware() -> MiddlewareStub:
    stub = MiddlewareStub(DEFAULT_TOKEN)
    stub.start()
    try:
        yield stub
    finally:
        stub.stop()


def _wait_for_registration(worker: Worker, timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        registered = worker.evaluate(
            "async () => (await chrome.scripting.getRegisteredContentScripts("
            "{ ids: ['content-main'] })).length"
        )
        if registered:
            return
        time.sleep(0.05)
    raise AssertionError("content.js was not registered in the MAIN world")


@pytest.fixture(scope="session")
def browser_factory(pytestconfig: pytest.Config) -> Callable[..., Harness]:
    contexts: list[BrowserContext] = []
    headed = bool(pytestconfig.getoption("--headed")) or bool(os.environ.get("PWDEBUG"))
    slow_mo = int(pytestconfig.getoption("--slowmo"))

    with sync_playwright() as playwright:

        def launch(
            *,
            chat_origin: str,
            converter_url: str,
            middleware_url: str,
            name: str,
        ) -> Harness:
            build = build_patched_extension(
                chat_origin=chat_origin,
                converter_url=converter_url,
                middleware_url=middleware_url,
                token=DEFAULT_TOKEN,
                destination=BUILD_ROOT / f"extension-{name}",
            )
            assert build.is_complete(), build.replacements
            profile = BUILD_ROOT / f"profile-{name}"
            if profile.exists():
                shutil.rmtree(profile)
            profile.mkdir(parents=True)
            context = playwright.chromium.launch_persistent_context(
                str(profile),
                channel="chromium",
                headless=not headed,
                slow_mo=slow_mo,
                args=[
                    f"--disable-extensions-except={build.destination}",
                    f"--load-extension={build.destination}",
                    "--no-first-run",
                    "--no-default-browser-check",
                ],
            )
            context.set_default_timeout(20_000)
            contexts.append(context)
            workers = context.service_workers
            worker = workers[0] if workers else context.wait_for_event("serviceworker")
            _wait_for_registration(worker)
            return Harness(
                build=build,
                context=context,
                worker=worker,
                extension_id=worker.url.split("/")[2],
            )

        try:
            yield launch
        finally:
            for context in contexts:
                context.close()


@pytest.fixture(scope="session")
def stub_harness(
    browser_factory,
    chat_site: str,
    converter: ConverterStub,
    middleware: MiddlewareStub,
) -> Harness:
    return browser_factory(
        chat_origin=chat_site,
        converter_url=f"{converter.base_url}/convertir",
        middleware_url=f"{middleware.base_url}/api/interactions/protect",
        name="stub",
    )


@pytest.fixture(scope="session")
def service_worker(stub_harness: Harness) -> Worker:
    return stub_harness.worker


@pytest.fixture(scope="session")
def extension_id(stub_harness: Harness) -> str:
    return stub_harness.extension_id


@pytest.fixture(autouse=True)
def deterministic_state(
    service_worker: Worker,
    converter: ConverterStub,
    middleware: MiddlewareStub,
) -> None:
    service_worker.evaluate(
        "(value) => chrome.storage.local.set({ activo: value })", True
    )
    converter.requests.clear()
    converter.markdown = DEFAULT_MARKDOWN
    converter.status = 200
    middleware.requests.clear()
    middleware.status = 200
    middleware.protect = default_protect


@pytest.fixture
def page(stub_harness: Harness, request: pytest.FixtureRequest) -> Page:
    page = stub_harness.context.new_page()
    try:
        with recording(stub_harness, request):
            yield page
    finally:
        page.close()


@pytest.fixture(scope="session")
def stack():
    from support.stack import docker_available, running_stack

    if not docker_available():
        pytest.skip("Docker is not available; the full-system tier needs Docker")
    with running_stack() as running:
        yield running


@pytest.fixture(scope="session")
def stack_harness(browser_factory, stack, chat_site: str) -> Harness:
    return browser_factory(
        chat_origin=chat_site,
        converter_url=f"{stack.converter_url}/convertir",
        middleware_url=f"{stack.api_url}/api/interactions/protect",
        name="stack",
    )


@pytest.fixture
def stack_page(stack_harness: Harness, request: pytest.FixtureRequest) -> Page:
    page = stack_harness.context.new_page()
    try:
        with recording(stack_harness, request):
            yield page
    finally:
        page.close()
