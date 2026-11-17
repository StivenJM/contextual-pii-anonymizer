"""Local HTTP servers used as test doubles and as the page under observation."""

from __future__ import annotations

import json
import re
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from http.server import (
    BaseHTTPRequestHandler,
    SimpleHTTPRequestHandler,
    ThreadingHTTPServer,
)
from pathlib import Path

DEFAULT_TOKEN = "e2e-middleware-token"
DEFAULT_MARKDOWN = "# Synthetic report\n\nContact: ana.torres@correo.com\n"
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE = re.compile(r"(?<!\d)(?:\+593[ -]?|0)9\d{8}(?!\d)")
FILENAME = re.compile(rb'filename="([^"]*)"')


@dataclass(frozen=True)
class RecordedRequest:
    method: str
    path: str
    headers: dict[str, str]
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    @property
    def json(self) -> dict:
        return json.loads(self.text or "{}")


Route = Callable[["StubServer", RecordedRequest], tuple[int, object]]


class _Handler(BaseHTTPRequestHandler):
    server_version = "e2e-stub/1.0"

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def _dispatch(self, method: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        recorder: list[RecordedRequest] = self.server.recorder  # type: ignore[attr-defined]
        routes: dict[tuple[str, str], Route] = self.server.routes  # type: ignore[attr-defined]
        request = RecordedRequest(
            method=method,
            path=self.path.split("?")[0],
            headers=dict(self.headers.items()),
            body=body,
        )
        recorder.append(request)
        route = routes.get((method, request.path))
        if route is None:
            self._send(404, {"error": "not found"})
            return
        status, payload = route(self.server, request)  # type: ignore[arg-type]
        self._send(status, payload)

    def _send(self, status: int, payload: object) -> None:
        if isinstance(payload, bytes):
            body = payload
            content_type = "text/plain; charset=utf-8"
        else:
            body = json.dumps(payload).encode("utf-8")
            content_type = "application/json"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        return


class StubServer:
    def __init__(self, routes: dict[tuple[str, str], Route], name: str) -> None:
        self.name = name
        self.routes = routes
        self.requests: list[RecordedRequest] = []
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> str:
        server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        server.routes = self.routes  # type: ignore[attr-defined]
        server.recorder = self.requests  # type: ignore[attr-defined]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self._server = server
        self._thread = thread
        return self.base_url

    @property
    def base_url(self) -> str:
        if self._server is None:
            raise RuntimeError(f"{self.name} is not running")
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def reset(self) -> None:
        self.requests.clear()


class ConverterStub(StubServer):
    """Behaves like the document conversion service, without MarkItDown."""

    def __init__(self, token: str = DEFAULT_TOKEN) -> None:
        self.token = token
        self.markdown = DEFAULT_MARKDOWN
        self.status = 200
        self.delay = 0.0
        self.error = {"ok": False, "error": "synthetic failure"}
        super().__init__({("POST", "/convertir"): self._convert}, "converter")

    def _convert(
        self, _server: StubServer, request: RecordedRequest
    ) -> tuple[int, object]:
        if request.headers.get("X-Token") != self.token:
            return 401, {"ok": False, "error": "No autorizado"}
        if self.status != 200:
            return self.status, self.error
        if self.delay:
            time.sleep(self.delay)
        match = FILENAME.search(request.body)
        filename = match.group(1).decode("utf-8") if match else ""
        return 200, {
            "ok": True,
            "markdown": self.markdown,
            "nombre_original": filename,
        }

    @property
    def last_filename(self) -> str:
        for request in reversed(self.requests):
            match = FILENAME.search(request.body)
            if match:
                return match.group(1).decode("utf-8")
        return ""


class MiddlewareStub(StubServer):
    """Behaves like the protection endpoint, with a deterministic protection rule."""

    def __init__(self, token: str = DEFAULT_TOKEN) -> None:
        self.token = token
        self.status = 200
        self.protect: Callable[[str], str] = default_protect
        self.operations: list[dict[str, object]] | None = None
        self.warnings: list[str] = []
        self.delay = 0.0
        super().__init__(
            {("POST", "/api/interactions/protect"): self._protect},
            "middleware",
        )

    def _protect(
        self, _server: StubServer, request: RecordedRequest
    ) -> tuple[int, object]:
        if self.status != 200:
            return self.status, {"message": "synthetic protection failure"}
        if self.delay:
            time.sleep(self.delay)
        payload = request.json
        original = payload.get("text", "")
        protected = self.protect(original)
        operations = self.operations
        if operations is None:
            operations = default_operations(original)
        return 200, {
            "original_text": original,
            "protected_text": protected,
            "detections": [],
            "operations": operations,
            "mapping_gaps": [],
            "warnings": self.warnings,
        }

    @property
    def last_text(self) -> str:
        for request in reversed(self.requests):
            return request.json.get("text", "")
        return ""


def default_protect(text: str) -> str:
    protected = EMAIL.sub("<EMAIL>", text)
    return PHONE.sub("<PHONE>", protected)


def default_operations(text: str) -> list[dict[str, object]]:
    """Derive the operations a real response would report for the default rule."""
    operations: list[dict[str, object]] = []
    for match in EMAIL.finditer(text):
        operations.append(
            {
                "canonical_type": "EMAIL",
                "start": match.start(),
                "end": match.end(),
                "original_text": match.group(),
                "replacement": "<EMAIL>",
                "action": "REPLACE_WITH_LABEL",
                "mapping_gap": False,
            }
        )
    for match in PHONE.finditer(text):
        operations.append(
            {
                "canonical_type": "PHONE",
                "start": match.start(),
                "end": match.end(),
                "original_text": match.group(),
                "replacement": "<PHONE>",
                "action": "REPLACE_WITH_LABEL",
                "mapping_gap": False,
            }
        )
    return operations


class _QuietStaticHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args: object) -> None:
        return


class StaticSite:
    """Serves the fake chat pages from a directory."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> str:
        directory = str(self.directory)

        class Handler(_QuietStaticHandler):
            def __init__(self, *args: object, **kwargs: object) -> None:
                super().__init__(*args, directory=directory, **kwargs)  # type: ignore[arg-type]

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self._server = server
        self._thread = thread
        return self.base_url

    @property
    def base_url(self) -> str:
        if self._server is None:
            raise RuntimeError("static site is not running")
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
