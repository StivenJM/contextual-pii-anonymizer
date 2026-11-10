import copy
import hashlib
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.research.application import create_research_app

KEY = "test-research-key-with-at-least-32-characters"
TOKEN = "test-session-capability-with-at-least-32-characters"


@pytest.fixture
def client(monkeypatch, tmp_path):
    for name in (
        "RESEARCH_API_KEY_FILE",
        "RESEARCH_ENROLLMENT_KEY",
        "RESEARCH_ENROLLMENT_KEY_FILE",
        "RESEARCH_REQUIRE_ENROLLMENT",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("RESEARCH_ENABLED", "true")
    monkeypatch.setenv("RESEARCH_API_KEY", KEY)
    monkeypatch.setenv("RESEARCH_STORAGE_PATH", str(tmp_path / "capture.sqlite3"))
    with TestClient(create_research_app()) as client:
        yield client


def start(client, **overrides):
    body = {
        "session_id": str(uuid4()),
        "upload_token": TOKEN,
        "protocol_version": "research-v1",
        "consent": True,
        "training_consent": False,
        "provider": "chatgpt",
    } | overrides
    response = client.post(
        "/api/research/sessions", json=body, headers={"X-Research-Key": KEY}
    )
    assert response.status_code == 201, response.text
    return body["session_id"]


def batch():
    return {
        "schema_version": 1,
        "events": [
            {
                "event_id": str(uuid4()),
                "role": "user",
                "text": "  Synthetic prompt\n",
                "captured_at": "2026-10-29T12:00:00Z",
                "task_id": "A",
            },
            {
                "event_id": str(uuid4()),
                "role": "assistant",
                "text": "Synthetic answer",
                "captured_at": "2026-10-29T12:01:00Z",
                "task_id": "A",
            },
        ],
    }


def finish(client, session_id, body, token=TOKEN):
    return client.put(
        f"/api/research/sessions/{session_id}/complete",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
    )


def test_save_receipt_retry_export_and_withdraw(client):
    session = start(client)
    body = batch()
    saved = finish(client, session, body)
    assert saved.status_code == 200
    receipt = saved.json()["receipt_id"]
    assert len(receipt) >= 24
    assert finish(client, session, body).json() == saved.json()
    assert client.get(f"/api/research/records/{receipt}").status_code == 401
    exported = client.get(
        f"/api/research/records/{receipt}", headers={"X-Research-Key": KEY}
    )
    assert exported.status_code == 200
    assert exported.json()["events"] == body["events"]
    assert exported.json()["training_consent"] is False
    assert "upload_token" not in exported.text
    assert (
        client.delete(
            f"/api/research/sessions/{session}",
            headers={"Authorization": f"Bearer {TOKEN}"},
        ).status_code
        == 204
    )
    assert (
        client.get(
            f"/api/research/records/{receipt}", headers={"X-Research-Key": KEY}
        ).status_code
        == 404
    )


def test_conflicting_retry_cannot_overwrite_saved_data(client):
    session = start(client)
    body = batch()
    receipt = finish(client, session, body).json()["receipt_id"]
    changed = copy.deepcopy(body)
    changed["events"][0]["text"] = "changed"
    assert finish(client, session, changed).status_code == 409
    assert (
        client.get(
            f"/api/research/records/{receipt}", headers={"X-Research-Key": KEY}
        ).json()["events"]
        == body["events"]
    )


def test_capture_is_disabled_by_default(client, monkeypatch):
    monkeypatch.delenv("RESEARCH_ENABLED")
    assert client.post("/api/research/sessions", json={}).status_code == 404


def test_authorization_and_consent_are_required(client):
    assert client.post("/api/research/sessions", json={}).status_code == 401
    body = {
        "session_id": str(uuid4()),
        "upload_token": TOKEN,
        "protocol_version": "research-v1",
        "consent": False,
        "provider": "chatgpt",
    }
    assert (
        client.post(
            "/api/research/sessions", json=body, headers={"X-Research-Key": KEY}
        ).status_code
        == 422
    )
    session = start(client)
    assert finish(client, session, batch(), token="wrong").status_code == 404


@pytest.mark.parametrize(
    "change", ["duplicate", "empty", "naive", "extra", "oversized"]
)
def test_invalid_batches_are_not_stored_or_echoed(client, change):
    session = start(client)
    body = batch()
    if change == "duplicate":
        body["events"][1]["event_id"] = body["events"][0]["event_id"]
    elif change == "empty":
        body["events"] = []
    elif change == "naive":
        body["events"][0]["captured_at"] = "2026-10-29T12:00:00"
    elif change == "extra":
        body["secret"] = "private-payload-never-echo"
    else:
        body["events"][0]["text"] = "private-payload-never-echo" * 60000
    rejected = finish(client, session, body)
    assert rejected.status_code in (413, 422)
    assert "private-payload-never-echo" not in rejected.text
    assert finish(client, session, batch()).status_code == 200


def test_concurrent_duplicate_uploads_have_one_receipt(client):
    session = start(client)
    body = batch()
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(lambda _: finish(client, session, body), range(4)))
    assert [r.status_code for r in responses] == [200] * 4
    assert len({r.json()["receipt_id"] for r in responses}) == 1


def test_expired_session_cannot_be_completed(client, monkeypatch):
    session = start(client)
    with sqlite3.connect(os.environ["RESEARCH_STORAGE_PATH"]) as db:
        db.execute("UPDATE research_sessions SET expires_at = 0")
    assert finish(client, session, batch()).status_code == 404


def test_rejected_completion_keeps_archive_bytes_unchanged(client):
    session = start(client)
    body = batch()
    assert finish(client, session, body).status_code == 200
    path = Path(os.environ["RESEARCH_STORAGE_PATH"])
    original = hashlib.sha256(path.read_bytes()).hexdigest()
    changed = copy.deepcopy(body)
    changed["events"][0]["text"] = "conflict"
    assert finish(client, session, changed).status_code == 409
    assert hashlib.sha256(path.read_bytes()).hexdigest() == original


def test_start_is_idempotent_but_does_not_change_existing_consent(client):
    session = str(uuid4())
    assert start(client, session_id=session) == session
    assert start(client, session_id=session) == session
    conflicting = {
        "session_id": session,
        "upload_token": TOKEN,
        "protocol_version": "research-v1",
        "consent": True,
        "provider": "chatgpt",
        "training_consent": True,
    }
    assert (
        client.post(
            "/api/research/sessions", json=conflicting, headers={"X-Research-Key": KEY}
        ).status_code
        == 409
    )


def test_purge_is_authorized_and_removes_expired_records(client):
    start(client)
    with sqlite3.connect(os.environ["RESEARCH_STORAGE_PATH"]) as db:
        db.execute("UPDATE research_sessions SET expires_at = 0")
    assert client.post("/api/research/purge-expired").status_code == 401
    assert client.post(
        "/api/research/purge-expired", headers={"X-Research-Key": KEY}
    ).json() == {"deleted": 1}


def test_normal_api_mount_keeps_existing_health_contract(client):
    from app.main import create_app

    normal = TestClient(create_app(), raise_server_exceptions=False)
    assert normal.get("/api/health").json() == {
        "message": "Contextual PII Anonymizer API",
        "version": "1.0.0",
        "status": "active",
    }
    assert (
        normal.post(
            "/api/research/sessions", json={}, headers={"X-Research-Key": KEY}
        ).status_code
        == 422
    )


def test_investigator_can_withdraw_by_receipt_but_receipt_alone_cannot(client):
    receipt = finish(client, start(client), batch()).json()["receipt_id"]
    path = f"/api/research/records/{receipt}"
    assert client.delete(path).status_code == 401
    assert client.delete(path, headers={"X-Research-Key": KEY}).status_code == 204
    assert client.get(path, headers={"X-Research-Key": KEY}).status_code == 404


def test_openapi_documents_bounded_start_and_complete_payloads(client):
    paths = client.get("/openapi.json").json()["paths"]
    start_schema = paths["/api/research/sessions"]["post"]["requestBody"]["content"][
        "application/json"
    ]["schema"]
    assert start_schema["properties"]["consent"]["const"] is True
    finish_schema = paths["/api/research/sessions/{session_id}/complete"]["put"][
        "requestBody"
    ]["content"]["application/json"]["schema"]
    assert finish_schema["properties"]["events"]["maxItems"] == 1000
    assert (
        finish_schema["properties"]["events"]["items"]["properties"]["text"][
            "maxLength"
        ]
        == 100000
    )


def test_enrollment_can_start_but_cannot_administer_records(client, monkeypatch):
    enrollment = "synthetic-enrollment-key-distinct-from-admin"
    monkeypatch.setenv("RESEARCH_ENROLLMENT_KEY", enrollment)
    session = str(uuid4())
    body = {
        "session_id": session,
        "upload_token": TOKEN,
        "protocol_version": "research-v1",
        "consent": True,
        "provider": "chatgpt",
    }
    headers = {"X-Research-Enrollment": enrollment}
    assert (
        client.post("/api/research/sessions", json=body, headers=headers).status_code
        == 201
    )
    receipt = finish(client, session, batch()).json()["receipt_id"]
    for method, path in (
        ("GET", f"/api/research/records/{receipt}"),
        ("DELETE", f"/api/research/records/{receipt}"),
        ("POST", "/api/research/purge-expired"),
    ):
        assert client.request(method, path, headers=headers).status_code == 401
        assert (
            client.request(
                method, path, headers={"X-Research-Key": enrollment}
            ).status_code
            == 401
        )
    assert (
        client.get(
            f"/api/research/records/{receipt}", headers={"X-Research-Key": KEY}
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/research/sessions", json=body, headers={"X-Research-Enrollment": KEY}
        ).status_code
        == 401
    )


def test_production_requires_distinct_enrollment_and_does_not_accept_admin_start(
    client, monkeypatch
):
    monkeypatch.setenv("RESEARCH_REQUIRE_ENROLLMENT", "true")
    assert client.get("/api/research/health").status_code == 503
    monkeypatch.setenv("RESEARCH_ENROLLMENT_KEY", KEY)
    assert client.get("/api/research/health").status_code == 503
    monkeypatch.setenv(
        "RESEARCH_ENROLLMENT_KEY", "distinct-synthetic-enrollment-secret-32chars"
    )
    assert client.get("/api/research/health").json() == {"status": "ready"}
    assert (
        client.post(
            "/api/research/sessions", json={}, headers={"X-Research-Key": KEY}
        ).status_code
        == 401
    )


def test_file_secrets_are_supported_without_echoing_unreadable_or_conflicting_values(
    client, monkeypatch, tmp_path
):
    path = tmp_path / "operator-key"
    path.write_text(KEY + "\n", encoding="utf-8")
    monkeypatch.delenv("RESEARCH_API_KEY")
    monkeypatch.setenv("RESEARCH_API_KEY_FILE", str(path))
    assert client.get("/api/research/health").status_code == 200
    start(client)
    monkeypatch.setenv("RESEARCH_API_KEY", "never-echo-this-secret")
    rejected = client.get("/api/research/health")
    assert rejected.status_code == 503
    assert "never-echo" not in rejected.text
    assert str(path) not in rejected.text
    monkeypatch.delenv("RESEARCH_API_KEY")
    path.unlink()
    assert client.get("/api/research/health").status_code == 503


def test_enrollment_cors_header_and_disabled_health(client, monkeypatch):
    response = client.options(
        "/api/research/sessions",
        headers={
            "Origin": "chrome-extension://synthetic",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "X-Research-Enrollment, Content-Type",
        },
    )
    assert response.status_code == 200
    monkeypatch.setenv("RESEARCH_ENABLED", "false")
    assert client.get("/api/research/health").status_code == 404


def test_normal_app_keeps_research_disabled_by_default(monkeypatch):
    from app.main import create_app

    monkeypatch.delenv("RESEARCH_ENABLED", raising=False)
    normal = TestClient(create_app())
    assert normal.get("/api/research/health").status_code == 404


def test_normal_app_serves_enabled_research_without_inference(client):
    from app.main import create_app

    normal = TestClient(create_app())
    # No lifespan ran, so the ordinary API has no database or inference client.
    assert not hasattr(normal.app.state, "container")
    session = start(normal)
    body = batch()
    saved = finish(normal, session, body)
    assert saved.status_code == 200
    receipt = saved.json()["receipt_id"]
    exported = normal.get(
        f"/api/research/records/{receipt}", headers={"X-Research-Key": KEY}
    )
    assert exported.status_code == 200
    assert exported.json()["events"] == body["events"]
