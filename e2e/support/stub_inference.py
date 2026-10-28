"""Deterministic stand-in for the BentoML inference service.

The Privacy Middleware talks to inference over HTTP with two fixed routes, so
the model can be replaced by a contract-faithful stub for integration testing.
"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL_ID = "openmed-pii-spanish-600m"
MODEL_VERSION = "stub-1"
NATIVE_TYPES = ["FIRSTNAME", "LASTNAME", "EMAIL", "PHONE", "NATIONAL_ID"]

NAME_PATTERN = re.compile(r"Ana Torres")


def detections(text: str) -> list[dict]:
    found: list[dict] = []
    for match in NAME_PATTERN.finditer(text):
        first_start, first_end = match.start(), match.start() + 3
        last_start, last_end = match.start() + 4, match.end()
        found.append(
            {
                "native_type": "FIRSTNAME",
                "text": text[first_start:first_end],
                "start": first_start,
                "end": first_end,
                "confidence": 0.99,
            }
        )
        found.append(
            {
                "native_type": "LASTNAME",
                "text": text[last_start:last_end],
                "start": last_start,
                "end": last_end,
                "confidence": 0.99,
            }
        )
    return found


class Handler(BaseHTTPRequestHandler):
    server_version = "inference-stub/1.0"

    def do_GET(self) -> None:
        if self.path == "/readyz":
            self._send(200, {"status": "ok"})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        payload = json.loads(self.rfile.read(length) or b"{}")
        if self.path == "/models":
            self._send(
                200,
                {
                    "models": [
                        {
                            "id": MODEL_ID,
                            "name": "Spanish PII (stub)",
                            "version": MODEL_VERSION,
                            "description": (
                                "Deterministic stub used by integration tests."
                            ),
                            "native_entity_types": NATIVE_TYPES,
                        }
                    ]
                },
            )
            return
        if self.path == "/detect":
            text = str(payload.get("text", ""))
            self._send(
                200,
                {
                    "model_id": MODEL_ID,
                    "model_version": MODEL_VERSION,
                    "detections": detections(text),
                },
            )
            return
        self._send(404, {"error": "not found"})

    def _send(self, status: int, payload: object) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        return


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 3000), Handler).serve_forever()
