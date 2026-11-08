from __future__ import annotations

import subprocess

import pytest

from support.documents import write_docx
from support.waiting import open_chat, wait_for_received

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@pytest.mark.integration
def test_full_system_protects_a_docx_attachment(
    stack_page, chat_site, stack, tmp_path
) -> None:
    document = write_docx(
        tmp_path / "informe.docx",
        [
            "Informe de practica",
            "Estudiante: Ana Torres",
            "Correo: ana.torres@correo.com",
        ],
    )

    open_chat(stack_page, f"{chat_site}/chat.html")
    stack_page.set_input_files(
        "#file",
        {
            "name": "informe.docx",
            "mimeType": DOCX_MIME,
            "buffer": document.read_bytes(),
        },
    )

    received = wait_for_received(stack_page, timeout_ms=90_000)

    assert received["name"] == "informe_converted.txt"
    assert received["type"] == "text/plain"
    assert "ana.torres@correo.com" not in received["text"]
    assert "Ana Torres" not in received["text"]
    assert "@example.org" in received["text"]


@pytest.mark.integration
def test_existing_api_http_and_postgresql_contracts(stack) -> None:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-p",
            stack.project,
            "exec",
            "-T",
            "-e",
            "RUN_DATABASE_INTEGRATION=1",
            "api",
            "uv",
            "run",
            "--frozen",
            "pytest",
            "tests/integration",
            "-q",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-4000:]
