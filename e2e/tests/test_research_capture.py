"""Real Chromium -> extension -> real model-free API -> SQLite, synthetic text only."""

import os
import re
import socket
import sqlite3
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from playwright.sync_api import expect

from support.waiting import open_chat, wait_for_received

ROOT = Path(__file__).resolve().parents[2]
KEY = "synthetic-research-key-with-at-least-32-characters"
ENROLLMENT = "synthetic-enrollment-only-code-at-least-32-characters"


@pytest.fixture
def research_api(tmp_path, request):
    python = (
        ROOT
        / "api"
        / ".venv"
        / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    if not python.exists():
        pytest.skip(
            "Prepare the API virtual environment before research browser tests."
        )
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    origin = f"http://127.0.0.1:{port}"
    env = os.environ | {
        "RESEARCH_ENABLED": "true",
        "RESEARCH_API_KEY": KEY,
        "RESEARCH_ENROLLMENT_KEY": ENROLLMENT,
        "RESEARCH_REQUIRE_ENROLLMENT": "true"
        if request.node.callspec.params.get("scenario") == "campus"
        else "false",
        "RESEARCH_STORAGE_PATH": str(tmp_path / "archive.sqlite3"),
    }
    process = subprocess.Popen(
        [
            str(python),
            "-m",
            "uvicorn",
            "app.research.application:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-access-log",
        ],
        cwd=ROOT / "api",
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    try:
        for _ in range(100):
            if process.poll() is not None:
                pytest.fail("Model-free research API exited before startup.")
            try:
                if httpx.get(f"{origin}/openapi.json", timeout=1).status_code == 200:
                    break
            except httpx.TransportError:
                time.sleep(0.1)
        else:
            pytest.fail("Model-free research API startup timeout.")
        yield origin
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.mark.parametrize(
    "scenario",
    [
        "normal",
        "navigation",
        "response_lost",
        "quota",
        "reload",
        "other_tab",
        "campus",
        "send_later",
        "mobile_composer",
        "mobile_composer_enter",
    ],
)
def test_research_session_roundtrip_without_inference(
    browser_factory, chat_site, research_api, converter, middleware, scenario, tmp_path
):
    harness = browser_factory(
        chat_origin=chat_site,
        converter_url=f"{converter.base_url}/convertir",
        middleware_url=f"{research_api}/api/interactions/protect",
        name="research-" + uuid4().hex[:8],
        additional_origins=(middleware.base_url,) if scenario == "other_tab" else (),
        research_origin=research_api if scenario == "campus" else None,
    )
    page = harness.context.new_page()
    popup = harness.context.new_page()
    try:
        page.goto(f"{chat_site}/research-chat.html")
        page.locator("textarea").wait_for()
        if scenario in ("mobile_composer", "mobile_composer_enter"):
            # Reproduce the semantic attributes supplied from the live composer.
            # Do not retain provider-generated classes, signal IDs or user text.
            page.locator("textarea").evaluate("""el => {
                el.removeAttribute('data-research-editor');
                el.id = 'mobile-composer-prompt';
                el.name = 'prompt';
                el.setAttribute('data-mobile-composer-prompt', '');
                el.setAttribute('aria-label', 'Chat with ChatGPT');
                el.setAttribute('placeholder', 'Ask ChatGPT');
                el.addEventListener('keydown', event => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        el.form.requestSubmit();
                    }
                });
            }""")
        if scenario == "send_later":
            page.evaluate("""() => {
                const send = document.querySelector('[data-research-send]');
                send.style.display = 'none';
                document.querySelector('textarea').addEventListener('input', () => {
                    send.style.display = '';
                });
            }""")
        popup.goto(f"chrome-extension://{harness.extension_id}/popup.html")
        expect(popup.locator("#researchTitle")).to_have_text(
            "Captura para investigación (solo texto)"
        )
        expect(popup.locator("#researchStart")).to_have_text("Iniciar en esta pestaña")
        expect(popup.locator("#researchFinish")).to_have_text(
            "Finalizar y guardar / reintentar"
        )
        popup.locator("#researchKey").fill(ENROLLMENT if scenario == "campus" else KEY)
        if scenario == "campus":
            expect(popup.locator("#researchKeyLabel")).to_have_text(
                "Código de participación del estudio"
            )
            expect(popup.locator("#researchEndpoint")).to_have_text(research_api)
        popup.locator("#researchConsent").check()
        page.bring_to_front()
        popup.locator("#researchStart").evaluate("el => el.click()")
        page.wait_for_function(
            "document.querySelector('#research-capture-indicator')"
            "?.textContent.includes('Captura activa')"
        )
        expect(popup.locator("#researchConsent")).to_be_disabled()
        expect(popup.locator("#researchTraining")).to_be_disabled()
        if scenario == "send_later":
            # Activation must not weaken the send-time guard while Send is absent.
            page.locator("textarea").evaluate(
                "el => { el.value = 'Blocked synthetic draft'; }"
            )
            page.locator("textarea").press("Enter")
            expect(page.locator("#research-capture-indicator")).to_contain_text(
                "se bloqueó"
            )
            assert page.evaluate("window.sentPrompts.length") == 0
            assert (
                harness.worker.evaluate(
                    "async () => (await chrome.storage.local.get('researchState'))"
                    ".researchState.session.events.length"
                )
                == 0
            )
        expect(popup.locator("#researchSetTask")).to_be_enabled()
        popup.locator("#researchSetTask").evaluate("el => el.click()")
        expect(popup.locator("#researchSetTask")).to_be_enabled()
        if scenario == "quota":
            harness.worker.evaluate("""() => {
                globalThis.savedSet = chrome.storage.local.set;
                chrome.storage.local.set = (values) => {
                    if (values.researchState?.session?.events?.length) {
                        return Promise.reject(new Error('synthetic storage quota'));
                    }
                    return savedSet.call(chrome.storage.local, values);
                };
            }""")
        prompt = "  Synthetic student: Alex, alex@example.invalid\n"
        page.locator("textarea").fill(prompt)
        if scenario == "mobile_composer_enter":
            page.locator("textarea").press("Enter")
        else:
            page.locator("[data-research-send]").click()
        if scenario == "quota":
            expect(page.locator("#research-capture-indicator")).to_contain_text(
                "se bloqueó"
            )
            assert page.evaluate("window.sentPrompts.length") == 0
            harness.worker.evaluate("() => { chrome.storage.local.set = savedSet; }")
            page.locator("[data-research-send]").click()
        page.wait_for_function("window.sentPrompts.length === 1")
        assert page.evaluate("window.sentPrompts[0]") == prompt
        page.wait_for_function(
            "document.querySelector('[data-research-role=assistant]')"
            "?.textContent === 'Synthetic complete reply'"
        )
        page.wait_for_timeout(350)
        if scenario == "navigation":
            page.evaluate("""() => {
                history.pushState({}, '', '/old-conversation');
                const previous = document.createElement('div');
                previous.dataset.researchRole = 'assistant';
                previous.textContent = 'Historical unrelated reply';
                document.querySelector('#history').append(previous);
            }""")
            page.wait_for_timeout(350)
        if scenario == "reload":
            page.reload()
            expect(page.locator("#research-capture-indicator")).to_contain_text(
                "en pausa"
            )
        if scenario == "other_tab":
            harness.worker.evaluate(
                """(url) => {
                    globalThis.savedFetch = fetch;
                    globalThis.fetch = (input, options) => savedFetch(
                        String(input).endsWith('/api/interactions/protect')
                            ? url : input, options);
                }""",
                f"{middleware.base_url}/api/interactions/protect",
            )
            other = harness.context.new_page()
            try:
                open_chat(other, f"{chat_site}/chat.html")
                other.set_input_files(
                    "#file",
                    {
                        "name": "synthetic.pdf",
                        "mimeType": "application/pdf",
                        "buffer": b"%PDF-1.4\nfixture\n%%EOF",
                    },
                )
                assert "<EMAIL>" in wait_for_received(other)["text"]
            finally:
                other.close()
        if scenario == "response_lost":
            harness.worker.evaluate("""() => {
                globalThis.savedFetch = fetch;
                let dropped = false;
                globalThis.fetch = async (input, options) => {
                    const response = await savedFetch(input, options);
                    if (!dropped && response.ok &&
                        String(input).endsWith('/complete')) {
                        dropped = true;
                        throw new TypeError('synthetic response lost');
                    }
                    return response;
                };
            }""")
        # Unsupported attachments must not reach either model-backed service.
        page.locator("input[type=file]").set_input_files(
            {"name": "synthetic.txt", "mimeType": "text/plain", "buffer": b"fixture"}
        )
        popup.locator("#researchFinish").evaluate("el => el.click()")
        committed_receipt = None
        if scenario == "response_lost":
            expect(popup.locator("#researchStatus")).to_contain_text(
                "No se pudo conectar con la API de investigación"
            )
            assert popup.locator("#researchReceipt").input_value() == ""
            with sqlite3.connect(tmp_path / "archive.sqlite3") as db:
                rows = db.execute(
                    "SELECT receipt_id FROM research_sessions "
                    "WHERE receipt_id IS NOT NULL"
                ).fetchall()
            assert len(rows) == 1
            committed_receipt = rows[0][0]
            popup.locator("#researchFinish").evaluate("el => el.click()")
        expect(popup.locator("#researchReceipt")).to_have_value(
            re.compile(r"^[A-Za-z0-9_-]{32}$"), timeout=20000
        )
        receipt = popup.locator("#researchReceipt").input_value()
        if committed_receipt:
            assert receipt == committed_receipt
        exported = httpx.get(
            f"{research_api}/api/research/records/{receipt}",
            headers={"X-Research-Key": KEY},
        )
        assert exported.status_code == 200
        record = exported.json()
        assert record["capture_status"] == (
            "interrupted" if scenario in ("navigation", "reload") else "complete"
        )
        assert [(e["role"], e["text"]) for e in record["events"]] == [
            ("user", prompt),
            ("assistant", "Synthetic complete reply"),
        ]
        assert all(e["task_id"] == "A" for e in record["events"])
        local = harness.worker.evaluate(
            "async () => "
            "(await chrome.storage.local.get('researchState')).researchState"
        )
        assert local["session"] is None
        assert "events" not in local["receipt"]
        assert len(converter.requests) == (1 if scenario == "other_tab" else 0)
        assert len(middleware.requests) == (1 if scenario == "other_tab" else 0)
        screenshot = os.environ.get("RESEARCH_QA_SCREENSHOT")
        if scenario == "normal" and screenshot:
            popup.locator("body").screenshot(path=screenshot)
        if scenario == "normal":
            page.locator("textarea").fill("Not part of the finished session")
            page.locator("[data-research-send]").click()
            page.wait_for_function("window.sentPrompts.length === 2")
            assert (
                harness.worker.evaluate(
                    "async () => (await chrome.storage.local.get('researchState'))"
                    ".researchState.session"
                )
                is None
            )
    finally:
        page.close()
        popup.close()


@pytest.mark.parametrize(
    "startup_case",
    ["history", "missing_editor", "unrelated_textarea", "hidden_mobile_composer"],
)
def test_research_startup_rejection_preserves_setup(
    browser_factory, chat_site, research_api, converter, startup_case, tmp_path
):
    harness = browser_factory(
        chat_origin=chat_site,
        converter_url=f"{converter.base_url}/convertir",
        middleware_url=f"{research_api}/api/interactions/protect",
        name="research-start-" + uuid4().hex[:8],
    )
    page = harness.context.new_page()
    popup = harness.context.new_page()
    try:
        page.goto(f"{chat_site}/research-chat.html")
        page.locator("textarea").wait_for()
        if startup_case == "history":
            page.evaluate("""() => {
                const user = document.createElement('div');
                user.dataset.researchRole = 'user';
                user.textContent = 'Unrelated earlier synthetic message';
                document.querySelector('#history').append(user);
            }""")
        elif startup_case == "unrelated_textarea":
            page.locator("textarea").evaluate(
                "el => el.removeAttribute('data-research-editor')"
            )
        elif startup_case == "hidden_mobile_composer":
            page.locator("textarea").evaluate("""el => {
                el.removeAttribute('data-research-editor');
                el.setAttribute('data-mobile-composer-prompt', '');
                el.style.display = 'none';
            }""")
        else:
            page.locator("textarea").evaluate("el => el.remove()")
        popup.goto(f"chrome-extension://{harness.extension_id}/popup.html")
        popup.locator("#researchKey").fill(KEY)
        popup.locator("#researchConsent").check()
        popup.locator("#researchTraining").uncheck()
        popup.locator("#researchStart").scroll_into_view_if_needed()
        page.bring_to_front()
        popup.locator("#researchStart").evaluate("el => el.click()")
        expected = (
            "Esta conversación ya tiene mensajes"
            if startup_case == "history"
            else "No se encontró el editor"
        )
        expect(popup.locator("#researchStatus")).to_contain_text(expected)
        expect(popup.locator("#researchStatus")).to_be_in_viewport()
        expect(popup.locator("#researchKey")).to_have_value(KEY)
        expect(popup.locator("#researchProtocol")).to_have_value("research-v1")
        expect(popup.locator("#researchConsent")).to_be_checked()
        expect(popup.locator("#researchTraining")).not_to_be_checked()
        expect(popup.locator("#researchStart")).to_be_enabled()
        assert (
            harness.worker.evaluate(
                "async () => (await chrome.storage.local.get('researchState'))"
                ".researchState?.session ?? null"
            )
            is None
        )
        assert not (tmp_path / "archive.sqlite3").exists()
        screenshot = os.environ.get("RESEARCH_START_QA_SCREENSHOT")
        if startup_case == "history" and screenshot:
            popup.locator("body").screenshot(path=screenshot)
    finally:
        page.close()
        popup.close()
