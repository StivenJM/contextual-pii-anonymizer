from __future__ import annotations

from playwright.sync_api import expect

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


def test_file_picker_reports_processing_then_completion(
    page, chat_site, converter
) -> None:
    converter.markdown = "# Synthetic report\n\nContact: ana.torres@correo.com\n"
    converter.delay = 1.0

    open_chat(page, f"{chat_site}/chat.html")
    page.set_input_files(
        "#file",
        {"name": "informe.pdf", "mimeType": "application/pdf", "buffer": PDF_BYTES},
    )

    status = page.locator("[data-attachment-status]")
    expect(status).to_have_attribute("data-attachment-status", "processing")
    expect(status.locator(".attachment-status-title")).to_have_text(
        "Procesando documento"
    )
    expect(status.locator(".attachment-status-text")).to_contain_text("informe.pdf")
    expect(status.locator(".attachment-status-icon")).to_be_visible()
    styles = status.locator(".attachment-status-card").evaluate(
        """el => {
            const icon = el.querySelector('.attachment-status-icon');
            const spinner = getComputedStyle(icon, '::before');
            return {
                display: getComputedStyle(el).display,
                radius: getComputedStyle(el).borderRadius,
                iconWidth: getComputedStyle(icon).width,
                spinnerAnimation: spinner.animationName,
                spinnerWidth: spinner.width
            };
        }"""
    )
    assert styles["display"] == "flex"
    assert styles["radius"] == "12px"
    assert styles["iconWidth"] == "34px"
    assert styles["spinnerAnimation"] == "attachment-status-spin"
    assert styles["spinnerWidth"] == "16px"
    expect(status).to_have_attribute("data-attachment-status", "done", timeout=5000)
    expect(status.locator(".attachment-status-title")).to_have_text(
        "Documento procesado"
    )

    received = wait_for_received(page)
    assert received["name"] == "informe_converted.txt"
    assert "ana.torres@correo.com" not in received["text"]
    expect(status).to_have_count(0, timeout=5000)


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
