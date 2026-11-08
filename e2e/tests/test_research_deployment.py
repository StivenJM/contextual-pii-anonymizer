"""Public preparation CLI tests; no university host or real credentials."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PREPARE = ROOT / "deployment" / "research" / "prepare.py"


@pytest.fixture(autouse=True)
def deterministic_state():
    """These CLI tests need no inherited browser-state fixture."""


def prepare(output, ip="10.20.30.40", *extra):
    return subprocess.run(
        [
            sys.executable,
            str(PREPARE),
            "--ip",
            ip,
            "--output",
            str(output),
            "--retention-days",
            "7",
            *extra,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_preparation_creates_distinct_secrets_and_narrow_extension_copy(tmp_path):
    output = tmp_path / "campus"
    source = ROOT / "browser-extension" / "extension"
    before = (source / "manifest.json").read_bytes()
    result = prepare(output)
    assert result.returncode == 0, result.stderr
    admin = (output / "secrets" / "admin.txt").read_text().strip()
    enrollment = (output / "secrets" / "enrollment.txt").read_text().strip()
    assert len(admin) >= 32
    assert len(enrollment) >= 32
    assert admin != enrollment
    assert admin not in result.stdout
    assert enrollment not in result.stdout
    manifest = json.loads((output / "extension" / "manifest.json").read_text())
    original = json.loads(before)
    assert set(manifest["host_permissions"]) - set(original["host_permissions"]) == {
        "https://10.20.30.40/*"
    }
    config = (output / "extension" / "research-config.js").read_text()
    assert '"https://10.20.30.40"' in config
    assert admin not in config
    assert enrollment not in config
    env = (output / ".env").read_text()
    assert "RESEARCH_RETENTION_DAYS=7" in env
    assert "RESEARCH_SERVER_IP=10.20.30.40" in env
    assert (source / "manifest.json").read_bytes() == before
    snapshot = (output / "secrets" / "admin.txt").read_bytes()
    assert prepare(output).returncode != 0
    assert (output / "secrets" / "admin.txt").read_bytes() == snapshot


@pytest.mark.parametrize(
    "ip",
    [
        "8.8.8.8",
        "127.0.0.1",
        "169.254.1.2",
        "10.1.2.3/24",
        "10.1.2.3\nINJECT=true",
        "example.com",
    ],
)
def test_preparation_rejects_non_campus_ipv4_without_creating_files(tmp_path, ip):
    output = tmp_path / "rejected"
    result = prepare(output, ip)
    assert result.returncode != 0
    assert "private RFC1918" in result.stderr
    assert not output.exists()


def test_preparation_rejects_invalid_protocol_before_any_write(tmp_path):
    output = tmp_path / "rejected"
    result = prepare(output, "10.0.0.2", "--protocol", "a\nINJECT=true")
    assert result.returncode != 0
    assert "Invalid protocol" in result.stderr
    assert not output.exists()
