from __future__ import annotations

from support.servers import DEFAULT_TOKEN
from support.waiting import open_chat, wait_for_received

PDF_BYTES = b"%PDF-1.4\n% fixture\n%%EOF\n"


def test_file_picker_converts_then_protects(
    page, chat_site, converter, middleware
) -> None:
    converter.markdown = "# Synthetic report\n\nContact: ana.torres@correo.com\n"

    open_chat(page, f"{chat_site}/chat.html")
    page.set_input_files(
        "#file",
        {"name": "informe.pdf", "mimeType": "application/pdf", "buffer": PDF_BYTES},
    )

    received = wait_for_received(page)

    assert received["name"] == "informe_converted.txt"
    assert received["type"] == "text/plain"
    assert "Contact: <EMAIL>" in received["text"]
    assert "ana.torres@correo.com" not in received["text"]

    assert converter.last_filename == "informe.pdf"
    assert converter.requests[-1].headers["X-Token"] == DEFAULT_TOKEN

    assert "ana.torres@correo.com" in middleware.last_text
    assert middleware.last_text.startswith("# Synthetic report")


def test_converted_file_is_not_intercepted_again(page, chat_site, converter) -> None:
    open_chat(page, f"{chat_site}/chat.html")
    page.set_input_files(
        "#file",
        {
            "name": "informe_converted.txt",
            "mimeType": "text/plain",
            "buffer": b"already protected",
        },
    )

    received = wait_for_received(page)

    assert received["name"] == "informe_converted.txt"
    assert received["text"] == "already protected"
    assert converter.requests == []
