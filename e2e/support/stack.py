"""Docker Compose orchestration for the full-system integration tier."""

from __future__ import annotations

import os
import socket
import subprocess
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = PROJECT_ROOT / "compose.test.yaml"
TOKEN = "e2e-middleware-token"


@dataclass(frozen=True)
class Stack:
    api_url: str
    converter_url: str
    project: str


def docker_available() -> bool:
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_http(url: str, *, timeout: float = 180.0, expected: int = 200) -> None:
    deadline = time.monotonic() + timeout
    last_error = ""
    while time.monotonic() < deadline:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == expected:
                return
            last_error = f"status {response.status_code}"
        except httpx.HTTPError as error:
            last_error = str(error)
        time.sleep(0.25)
    raise AssertionError(f"{url} did not become ready: {last_error}")


@contextmanager
def running_stack() -> Iterator[Stack]:
    project = f"cpa-e2e-{uuid.uuid4().hex[:8]}"
    api_port = free_port()
    converter_port = free_port()
    environment = {
        **os.environ,
        "API_PORT": str(api_port),
        "CONVERTER_PORT": str(converter_port),
        "E2E_MIDDLEWARE_TOKEN": TOKEN,
    }
    command = [
        "docker",
        "compose",
        "-p",
        project,
        "-f",
        str(COMPOSE_FILE),
    ]
    subprocess.run(
        [*command, "up", "-d", "--build", "--wait"],
        check=True,
        env=environment,
        timeout=1200,
    )
    try:
        api_url = f"http://127.0.0.1:{api_port}"
        converter_url = f"http://127.0.0.1:{converter_port}"
        wait_for_http(f"{api_url}/api/health", timeout=180.0)
        wait_for_http(f"{converter_url}/docs", timeout=180.0)
        yield Stack(api_url=api_url, converter_url=converter_url, project=project)
    finally:
        subprocess.run(
            [*command, "down", "-v", "--remove-orphans"],
            check=False,
            env=environment,
            timeout=300,
        )
