from __future__ import annotations

from support.waiting import wait_for_received

PDF_BYTES = b"%PDF-1.4\n% fixture\n%%EOF\n"


def test_disabled_extension_delivers_the_original_file(
    page, service_worker, chat_site, converter
) -> None:
    service_worker.evaluate(
        "(value) => chrome.storage.local.set({ activo: value })", False
    )

    page.goto(f"{chat_site}/chat.html")
    page.set_input_files(
        "#file",
        {"name": "informe.pdf", "mimeType": "application/pdf", "buffer": PDF_BYTES},
    )

    received = wait_for_received(page)

    assert received["name"] == "informe.pdf"
    assert received["type"] == "application/pdf"
    assert received["text"].startswith("%PDF-1.4")
    assert converter.requests == []
