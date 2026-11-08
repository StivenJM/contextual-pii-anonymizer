"""Isolated production Compose/TLS rehearsal with synthetic loopback data."""

import json
import os
import socket
import ssl
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def deterministic_state():
    """This Docker/TLS test needs no inherited browser-state fixture."""


@pytest.mark.integration
def test_production_collector_trusted_tls_separation_and_restart(tmp_path):
    project = "cpa-research-e2e-" + uuid4().hex[:10]
    admin = "synthetic-admin-secret-at-least-32-characters"
    enrollment = "synthetic-enrollment-secret-at-least-32-characters"
    for name, value in (("admin", admin), ("enrollment", enrollment)):
        path = tmp_path / f"{name}.txt"
        path.write_text(value, encoding="utf-8")
        path.chmod(0o444)
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = os.environ | {
        "RESEARCH_SERVER_IP": "127.0.0.1",  # Loopback override only for this test.
        "RESEARCH_HTTPS_PORT": str(port),
        "RESEARCH_ADMIN_SECRET_FILE": str(tmp_path / "admin.txt"),
        "RESEARCH_ENROLLMENT_SECRET_FILE": str(tmp_path / "enrollment.txt"),
        "RESEARCH_PROTOCOL_VERSION": "research-v1",
        "RESEARCH_RETENTION_DAYS": "1",
    }
    base = [
        "docker",
        "compose",
        "-f",
        str(ROOT / "compose.research.yaml"),
        "-p",
        project,
    ]

    def compose(*args, timeout=60):
        result = subprocess.run(
            base + list(args),
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        assert result.returncode == 0, result.stderr[-4000:]
        return result.stdout.strip()

    origin = f"https://127.0.0.1:{port}"
    try:
        config = json.loads(compose("config", "--format", "json"))
        assert set(config["services"]) == {"collector", "proxy"}
        assert "ports" not in config["services"]["collector"]
        assert config["services"]["collector"]["read_only"] is True
        compose("up", "--build", "--wait", "--wait-timeout", "90", "-d", timeout=420)
        cert = tmp_path / "root.crt"
        compose("cp", "proxy:/data/caddy/pki/authorities/local/root.crt", str(cert))
        original_ca = cert.read_bytes()
        with pytest.raises(httpx.ConnectError, match="CERTIFICATE_VERIFY_FAILED"):
            httpx.get(origin + "/api/research/health", timeout=5, trust_env=False)
        trust = ssl.create_default_context(cafile=str(cert))
        assert trust.check_hostname
        assert trust.verify_mode == ssl.CERT_REQUIRED
        with httpx.Client(
            base_url=origin, verify=trust, trust_env=False, timeout=10
        ) as client:
            assert client.get("/api/research/health").json() == {"status": "ready"}
            assert client.get("/docs").status_code == 404
            assert (
                client.post(
                    "/api/research/sessions", json={}, headers={"X-Research-Key": admin}
                ).status_code
                == 401
            )
            session, token = str(uuid4()), uuid4().hex + uuid4().hex
            headers = {"X-Research-Enrollment": enrollment}
            started = client.post(
                "/api/research/sessions",
                headers=headers,
                json={
                    "session_id": session,
                    "upload_token": token,
                    "protocol_version": "research-v1",
                    "consent": True,
                    "provider": "chatgpt",
                },
            )
            assert started.status_code == 201
            capability = {"Authorization": f"Bearer {token}"}
            body = {
                "schema_version": 1,
                "events": [
                    {
                        "event_id": str(uuid4()),
                        "role": "user",
                        "text": "Synthetic production rehearsal",
                        "captured_at": "2026-10-30T12:00:00Z",
                    }
                ],
            }
            saved = client.put(
                f"/api/research/sessions/{session}/complete",
                headers=capability,
                json=body,
            )
            assert saved.status_code == 200
            receipt = saved.json()["receipt_id"]
            record_path = f"/api/research/records/{receipt}"
            assert client.get(record_path, headers=headers).status_code == 401
            original = client.get(record_path, headers={"X-Research-Key": admin}).json()
            assert original["events"][0]["text"] == body["events"][0]["text"]
            compose("restart", "collector", "proxy")
            for _ in range(50):
                try:
                    if client.get("/api/research/health").status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                time.sleep(0.2)
            else:
                pytest.fail("Production collector did not recover after restart")
            assert (
                client.get(record_path, headers={"X-Research-Key": admin}).json()
                == original
            )
            assert (
                client.put(
                    f"/api/research/sessions/{session}/complete",
                    headers=capability,
                    json=body,
                ).json()
                == saved.json()
            )
            compose("cp", "proxy:/data/caddy/pki/authorities/local/root.crt", str(cert))
            assert cert.read_bytes() == original_ca
            assert (
                client.delete(
                    f"/api/research/sessions/{session}", headers=capability
                ).status_code
                == 204
            )
            assert (
                client.get(record_path, headers={"X-Research-Key": admin}).status_code
                == 404
            )
        for service in ("collector", "proxy"):
            container = compose("ps", "-q", service)
            result = subprocess.run(
                ["docker", "inspect", container],
                capture_output=True,
                text=True,
                timeout=20,
            )
            assert result.returncode == 0
            details = json.loads(result.stdout)[0]
            assert details["Config"]["User"] == "10001:10001"
            assert details["HostConfig"]["ReadonlyRootfs"] is True
    finally:
        # Only this randomly named test project and its synthetic volumes.
        compose("down", "--volumes", "--remove-orphans", timeout=90)
