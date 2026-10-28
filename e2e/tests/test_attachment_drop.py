from __future__ import annotations

from support.waiting import drop_document, wait_for_received

PDF_BYTES = "%PDF-1.4\n% fixture\n%%EOF\n"


def test_drop_zone_converts_then_protects(
    page, chat_site, converter, middleware
) -> None:
    converter.markdown = "# Synthetic report\n\nContact: ana.torres@correo.com\n"

    page.goto(f"{chat_site}/drop.html")
    drop_document(page, name="informe.pdf", mime="application/pdf", text=PDF_BYTES)

    received = wait_for_received(page)

    assert received["name"] == "informe_converted.txt"
    assert received["type"] == "text/plain"
    assert "ana.torres@correo.com" not in received["text"]
    assert converter.last_filename == "informe.pdf"
    assert "ana.torres@correo.com" in middleware.last_text
