from __future__ import annotations

import pytest
from playwright.sync_api import expect


@pytest.fixture(scope="module")
def chat_harness(browser_factory, chat_site, converter, middleware):
    return browser_factory(
        chat_origin=chat_site,
        converter_url=f"{converter.base_url}/convertir",
        middleware_url=f"{middleware.base_url}/api/interactions/protect",
        name="chat-protection",
    )


def open_protected_page(harness, chat_site, path):
    harness.worker.evaluate("() => chrome.storage.local.set({ chatProtection: true })")
    page = harness.context.new_page()
    page.goto(f"{chat_site}/{path}")
    page.locator("#prompt").wait_for()
    return page


def test_clean_message_sends_once_without_a_confirmation(
    chat_harness, chat_site, middleware
):
    page = open_protected_page(chat_harness, chat_site, "chat-protection-textarea.html")
    try:
        page.locator("#prompt").fill("Hola equipo")
        page.wait_for_timeout(300)
        assert len(middleware.requests) == 0
        page.locator("#send").click()
        page.wait_for_function("() => window.sentPrompts.length === 1")

        assert page.evaluate("() => window.sentPrompts") == ["Hola equipo"]
        assert len(middleware.requests) == 1
        assert page.locator("[data-chat-protection-card]").count() == 0
    finally:
        page.close()


def test_enabling_chat_protection_syncs_to_an_open_tab(chat_harness, chat_site):
    chat_harness.worker.evaluate(
        "() => chrome.storage.local.set({ chatProtection: false })"
    )
    page = chat_harness.context.new_page()
    try:
        page.goto(f"{chat_site}/chat-protection-textarea.html")
        page.locator("#prompt").fill("ana@example.com")
        chat_harness.worker.evaluate(
            "() => chrome.storage.local.set({ chatProtection: true })"
        )
        page.wait_for_timeout(500)
        page.locator("#send").click()

        card = page.locator("[data-chat-protection-card]")
        expect(card).to_have_count(1)
        expect(card.locator(".chat-protection-title")).to_have_text(
            "Se protegerá 1 dato personal"
        )
    finally:
        page.close()


def test_repeated_send_events_do_not_duplicate_review_or_send(
    chat_harness, chat_site, middleware
):
    page = open_protected_page(chat_harness, chat_site, "chat-protection-textarea.html")
    try:
        page.locator("#prompt").fill("Hola equipo")
        page.locator("#send").evaluate("el => { el.click(); el.click(); }")
        page.wait_for_function("() => window.sentPrompts.length === 1")

        assert page.evaluate("() => window.sentPrompts") == ["Hola equipo"]
        assert len(middleware.requests) == 1
        assert page.locator("[data-chat-protection-card]").count() == 0
    finally:
        page.close()


def test_changed_message_keeps_original_and_sends_exactly_protected_text(
    chat_harness, chat_site, middleware
):
    page = open_protected_page(chat_harness, chat_site, "chat-protection-textarea.html")
    try:
        original = "Hola ana@example.com, revisa esto"
        page.locator("#prompt").fill(original)
        page.locator("#send").click()

        card = page.locator("[data-chat-protection-card]")
        expect(card).to_have_count(1)
        expect(card.locator(".chat-protection-title")).to_have_text(
            "Se protegerá 1 dato personal"
        )
        placement = card.evaluate(
            """el => {
                const style = getComputedStyle(el);
                return {
                    position: style.position,
                    right: style.right,
                    bottom: style.bottom,
                    left: style.left,
                    top: style.top
                };
            }"""
        )
        assert placement["position"] == "fixed"
        assert placement["right"] == "16px"
        assert placement["bottom"] == "16px"
        assert page.evaluate("() => window.sentPrompts.length") == 0
        assert page.locator("#prompt").input_value() == original
        expect(page.locator("[data-chat-protection-highlight]")).to_have_count(1)

        card.get_by_role("button", name="Enviar versión protegida").click()
        page.wait_for_function("() => window.sentPrompts.length === 1")

        assert page.evaluate("() => window.sentPrompts") == [
            "Hola <EMAIL>, revisa esto"
        ]
        assert len(middleware.requests) == 1
        expect(card).to_have_count(0)
    finally:
        page.close()


def test_multiple_protected_spans_use_plural_copy_and_two_marks(
    chat_harness, chat_site
):
    page = open_protected_page(chat_harness, chat_site, "chat-protection-textarea.html")
    try:
        page.locator("#prompt").fill("ana@example.com y luis@example.com")
        page.locator("#send").click()

        card = page.locator("[data-chat-protection-card]")
        expect(card.locator(".chat-protection-title")).to_have_text(
            "Se protegerán 2 datos personales"
        )
        expect(page.locator("[data-chat-protection-highlight] span")).to_have_count(2)

        card.get_by_role("button", name="Enviar versión protegida").click()
        page.wait_for_function("() => window.sentPrompts.length === 1")
        assert page.evaluate("() => window.sentPrompts") == ["<EMAIL> y <EMAIL>"]
    finally:
        page.close()


def test_contenteditable_highlights_emoji_offsets_and_replays_protected_text(
    chat_harness, chat_site
):
    page = open_protected_page(
        chat_harness, chat_site, "chat-protection-contenteditable.html"
    )
    try:
        original = "😀 ana@example.com"
        page.locator("#prompt").fill(original)
        page.locator("#send").click()

        card = page.locator("[data-chat-protection-card]")
        expect(card).to_have_count(1)
        expect(card.locator(".chat-protection-title")).to_have_text(
            "Se protegerá 1 dato personal"
        )
        assert page.evaluate("() => CSS.highlights.has('chat-pii-protected')") is True
        assert page.evaluate("() => CSS.highlights.get('chat-pii-protected').size") >= 1

        card.get_by_role("button", name="Enviar versión protegida").click()
        page.wait_for_function("() => window.sentPrompts.length === 1")
        assert page.evaluate("() => window.sentPrompts") == ["😀 <EMAIL>"]
        expect(card).to_have_count(0)
    finally:
        page.close()


def test_enter_send_uses_the_same_single_protection_path(
    chat_harness, chat_site, middleware
):
    page = open_protected_page(
        chat_harness, chat_site, "chat-protection-contenteditable.html"
    )
    try:
        page.locator("#prompt").fill("Hola equipo")
        page.locator("#prompt").press("Enter")
        page.wait_for_function("() => window.sentPrompts.length === 1")

        assert page.evaluate("() => window.sentPrompts") == ["Hola equipo"]
        assert len(middleware.requests) == 1
    finally:
        page.close()


def test_conversation_change_invalidates_a_pending_review(
    chat_harness, chat_site, middleware
):
    middleware.delay = 0.8
    page = open_protected_page(chat_harness, chat_site, "chat-protection-textarea.html")
    try:
        page.locator("#prompt").fill("ana@example.com")
        page.locator("#send").click()
        page.wait_for_timeout(100)
        page.evaluate("() => history.pushState({}, '', '/otra-conversacion')")
        page.wait_for_timeout(1200)

        assert page.evaluate("() => window.sentPrompts.length") == 0
        assert page.locator("[data-chat-protection-card]").count() == 0
        assert len(middleware.requests) == 1
    finally:
        page.close()


def test_disabling_the_switch_invalidates_a_pending_review(
    chat_harness, chat_site, middleware
):
    middleware.delay = 0.8
    page = open_protected_page(chat_harness, chat_site, "chat-protection-textarea.html")
    try:
        page.locator("#prompt").fill("ana@example.com")
        page.locator("#send").click()
        page.wait_for_timeout(100)
        chat_harness.worker.evaluate(
            "() => chrome.storage.local.set({ chatProtection: false })"
        )
        page.wait_for_timeout(1200)

        assert page.evaluate("() => window.sentPrompts.length") == 0
        assert page.locator("[data-chat-protection-card]").count() == 0
    finally:
        chat_harness.worker.evaluate(
            "() => chrome.storage.local.set({ chatProtection: true })"
        )
        page.close()


def test_editing_invalidates_a_pending_review_and_requires_a_new_send(
    chat_harness, chat_site, middleware
):
    middleware.delay = 0.8
    page = open_protected_page(chat_harness, chat_site, "chat-protection-textarea.html")
    try:
        page.locator("#prompt").fill("ana@example.com")
        page.locator("#send").click()
        page.wait_for_timeout(100)
        page.locator("#prompt").fill("texto nuevo")
        page.wait_for_timeout(1000)

        assert page.evaluate("() => window.sentPrompts.length") == 0
        assert page.locator("[data-chat-protection-card]").count() == 0
        assert len(middleware.requests) == 1

        middleware.delay = 0.0
        page.locator("#send").click()
        page.wait_for_function("() => window.sentPrompts.length === 1")
        assert page.evaluate("() => window.sentPrompts") == ["texto nuevo"]
        assert len(middleware.requests) == 2
    finally:
        page.close()


def test_send_is_blocked_while_an_attachment_is_still_being_protected(
    chat_harness, chat_site, converter
):
    converter.delay = 1.0
    page = open_protected_page(chat_harness, chat_site, "chat-protection-textarea.html")
    try:
        page.set_input_files(
            "#file",
            {
                "name": "informe.pdf",
                "mimeType": "application/pdf",
                "buffer": b"%PDF-1.4\n% fixture\n%%EOF\n",
            },
        )
        page.locator("#prompt").fill("Hola equipo")
        page.locator("#send").click()

        expect(page.locator("[data-attachment-status]")).to_have_attribute(
            "data-attachment-status", "processing"
        )
        expect(page.locator("[data-chat-protection-card]")).to_have_count(0)
        assert page.evaluate("() => window.sentPrompts.length") == 0
        # Let the background attachment conversion finish before the next test.
        page.wait_for_timeout(1500)
    finally:
        page.close()


def test_api_error_keeps_the_draft_and_retry_can_recover(
    chat_harness, chat_site, middleware
):
    middleware.status = 500
    page = open_protected_page(chat_harness, chat_site, "chat-protection-textarea.html")
    try:
        original = "Hola ana@example.com"
        page.locator("#prompt").fill(original)
        page.locator("#send").click()

        card = page.locator("[data-chat-protection-card]")
        expect(card).to_have_count(1)
        expect(card.locator(".chat-protection-title")).to_have_text(
            "No se pudo revisar el mensaje"
        )
        assert page.evaluate("() => window.sentPrompts.length") == 0
        assert page.locator("#prompt").input_value() == original

        middleware.status = 200
        card.get_by_role("button", name="Reintentar revisión").click()
        expect(card.locator(".chat-protection-title")).to_have_text(
            "Se protegerá 1 dato personal"
        )
        card.get_by_role("button", name="Enviar versión protegida").click()
        page.wait_for_function("() => window.sentPrompts.length === 1")

        assert page.evaluate("() => window.sentPrompts") == ["Hola <EMAIL>"]
        assert len(middleware.requests) == 2
    finally:
        page.close()
