"""Deterministic waiting helpers.

The harness never uses a fixed sleep as synchronization. Positive conditions
wait for an observable state. Negative conditions ("the page never receives the
file") cannot be observed directly, so they sample a bounded window and fail as
soon as the forbidden state appears.
"""

from __future__ import annotations

import time
from typing import Any

DEFAULT_TIMEOUT_MS = 20_000


def wait_for_received(page: Any, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> dict:
    page.wait_for_function("() => window.__received !== null", timeout=timeout_ms)
    return page.evaluate("() => window.__received")


def assert_never_received(page: Any, seconds: float = 2.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if page.evaluate("() => window.__received !== null"):
            received = page.evaluate("() => window.__received")
            raise AssertionError(
                f"page received a file but should not have: {received}"
            )
        time.sleep(0.05)


def drop_document(page: Any, *, name: str, mime: str, text: str) -> None:
    page.evaluate(
        """
        ({ name, mime, text }) => {
          const bytes = new TextEncoder().encode(text);
          const file = new File([bytes], name, { type: mime });
          const data = new DataTransfer();
          data.items.add(file);
          const target = document.getElementById('drop');
          target.dispatchEvent(new DragEvent('dragenter', {
            bubbles: true, cancelable: true, composed: true, dataTransfer: data
          }));
          target.dispatchEvent(new DragEvent('dragover', {
            bubbles: true, cancelable: true, composed: true, dataTransfer: data
          }));
          target.dispatchEvent(new DragEvent('drop', {
            bubbles: true, cancelable: true, composed: true, dataTransfer: data
          }));
        }
        """,
        {"name": name, "mime": mime, "text": text},
    )
