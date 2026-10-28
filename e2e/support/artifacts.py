"""Trace recording for the debug workflow.

Trace artifacts serialize DOM snapshots, network headers, cookies, and request
bodies. In this repository the fixtures use synthetic data only, and the output
is written under a git-ignored directory so it never reaches version control.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

TRACE_DIRECTORY = Path(__file__).resolve().parents[1] / "test-results"
_UNSAFE = re.compile(r"[^A-Za-z0-9_.-]+")


def trace_path(node_id: str, harness_name: str) -> Path:
    safe = _UNSAFE.sub("_", node_id).strip("_")[:120]
    return TRACE_DIRECTORY / f"{safe}-{harness_name}.zip"


def failed(request) -> bool:
    report = getattr(request.node, "rep_call", None)
    return bool(report is not None and report.failed)


@contextmanager
def recording(harness, request) -> Iterator[None]:
    mode = request.config.getoption("pw_trace")
    if mode == "off":
        yield
        return

    harness.context.tracing.start(screenshots=True, snapshots=True, sources=True)
    try:
        yield
    finally:
        keep = mode == "on" or failed(request)
        destination = trace_path(request.node.nodeid, harness.build.destination.name)
        if keep:
            destination.parent.mkdir(parents=True, exist_ok=True)
        harness.context.tracing.stop(path=str(destination) if keep else None)
        if not keep and destination.exists():
            destination.unlink()
