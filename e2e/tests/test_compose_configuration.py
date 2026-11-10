"""Fast Docker Compose configuration contracts for the local development stack."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EXTENSION_ID = "a" * 32
RESEARCH_KEY = "synthetic-local-research-key-at-least-32-chars"
INTERPOLATED = {
    "EXTENSION_ID_CHROME",
    "MIDDLEWARE_SECRET",
    "RESEARCH_API_KEY",
    "RESEARCH_PROTOCOL_VERSION",
    "RESEARCH_RETENTION_DAYS",
}


def _compose_available() -> bool:
    if shutil.which("docker") is None:
        return False
    result = subprocess.run(
        ["docker", "compose", "version"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode == 0


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _compose_available(), reason="Docker Compose is not available"
    ),
]


def compose_result(
    tmp_path: Path, files: list[str], values: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    """Resolve Compose files against isolated interpolation values.

    The repository's private root ``.env`` must never influence these
    assertions, so every call uses a temporary ``--env-file`` and strips the
    same names from the inherited environment.
    """
    env_file = tmp_path / "compose.env"
    env_file.write_text(
        "".join(f"{name}={value}\n" for name, value in values.items()),
        encoding="utf-8",
    )
    environment = os.environ.copy()
    for name in INTERPOLATED:
        environment.pop(name, None)
    command = ["docker", "compose", "--env-file", str(env_file)]
    for name in files:
        command.extend(["-f", str(ROOT / name)])
    command.extend(["config", "--format", "json"])
    return subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=120,
    )


def compose_config(tmp_path: Path, files: list[str], values: dict[str, str]) -> dict:
    result = compose_result(tmp_path, files, values)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def published_port(service: dict) -> dict:
    ports = service["ports"]
    assert len(ports) == 1
    return ports[0]


def test_default_stack_starts_converter_with_extension_configuration(
    tmp_path: Path,
) -> None:
    config = compose_config(
        tmp_path, ["compose.yaml"], {"EXTENSION_ID_CHROME": EXTENSION_ID}
    )
    services = config["services"]

    assert set(services) >= {"db", "inference", "api", "converter"}
    converter = services["converter"]
    assert (
        converter["build"]["context"]
        .replace("\\", "/")
        .endswith("browser-extension/backend")
    )
    assert published_port(converter) == {
        "mode": "ingress",
        "target": 5000,
        "published": "5000",
        "host_ip": "127.0.0.1",
        "protocol": "tcp",
    }
    assert converter["environment"]["EXTENSION_ID_CHROME"] == EXTENSION_ID
    background = (ROOT / "browser-extension/extension/background.js").read_text(
        encoding="utf-8"
    )
    token = re.search(r"(?m)^const SECRET_TOKEN = '([^']+)';$", background)
    assert token is not None
    assert converter["environment"]["MIDDLEWARE_SECRET"] == token.group(1)
    assert "5000/docs" in " ".join(converter["healthcheck"]["test"])


def test_default_stack_keeps_internal_services_and_research_disabled(
    tmp_path: Path,
) -> None:
    config = compose_config(
        tmp_path, ["compose.yaml"], {"EXTENSION_ID_CHROME": EXTENSION_ID}
    )
    services = config["services"]

    assert published_port(services["api"])["host_ip"] == "127.0.0.1"
    assert "ports" not in services["db"]
    assert "ports" not in services["inference"]
    assert set(services["api"]["depends_on"]) == {"db", "inference"}
    assert "converter" not in services["api"]["depends_on"]
    assert "RESEARCH_ENABLED" not in (services["api"].get("environment") or {})
    assert "research_archive" not in (config.get("volumes") or {})
    assert "pgadmin" not in services


def test_research_override_adds_persistent_archive_to_the_api(tmp_path: Path) -> None:
    config = compose_config(
        tmp_path,
        ["compose.yaml", "compose.research.dev.yaml"],
        {"EXTENSION_ID_CHROME": EXTENSION_ID, "RESEARCH_API_KEY": RESEARCH_KEY},
    )
    services = config["services"]
    api = services["api"]
    environment = api["environment"]

    assert set(services) == {"db", "inference", "api", "converter"}
    assert environment["RESEARCH_ENABLED"] == "true"
    assert environment["RESEARCH_API_KEY"] == RESEARCH_KEY
    assert environment["RESEARCH_STORAGE_PATH"] == "/data/research/capture.sqlite3"
    assert environment["RESEARCH_PROTOCOL_VERSION"] == "research-v1"
    assert environment["RESEARCH_RETENTION_DAYS"] == "7"
    mounts = [volume for volume in api["volumes"] if volume["type"] == "volume"]
    assert [mount["target"] for mount in mounts] == ["/data/research"]
    assert "research_archive" in config["volumes"]
    assert set(api["depends_on"]) == {"db", "inference"}


def test_research_override_requires_a_local_operator_key(tmp_path: Path) -> None:
    result = compose_result(
        tmp_path,
        ["compose.yaml", "compose.research.dev.yaml"],
        {"EXTENSION_ID_CHROME": EXTENSION_ID},
    )

    assert result.returncode != 0
    assert "RESEARCH_API_KEY" in result.stderr
