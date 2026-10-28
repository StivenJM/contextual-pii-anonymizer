from __future__ import annotations

from support.waiting import assert_never_received, open_chat

PDF_BYTES = b"%PDF-1.4\n% fixture\n%%EOF\n"
FILE = {"name": "informe.pdf", "mimeType": "application/pdf", "buffer": PDF_BYTES}


def test_conversion_failure_keeps_the_file_away_from_the_page(
    page, chat_site, converter
) -> None:
    converter.status = 401

    open_chat(page, f"{chat_site}/chat.html")
    page.set_input_files("#file", FILE)

    assert_never_received(page)
    assert len(converter.requests) == 1


def test_protection_failure_keeps_the_file_away_from_the_page(
    page, chat_site, middleware, converter
) -> None:
    middleware.status = 500

    open_chat(page, f"{chat_site}/chat.html")
    page.set_input_files("#file", FILE)

    assert_never_received(page)
    assert len(converter.requests) == 1
    assert len(middleware.requests) == 1
