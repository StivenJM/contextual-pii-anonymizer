import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app() -> FastAPI:
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_root_describes_the_service(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Contextual PII Anonymizer API",
        "version": "1.0.0",
        "status": "active",
    }


def test_health_reports_service_status(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Contextual PII Anonymizer API",
        "version": "1.0.0",
        "status": "active",
    }


def test_unknown_endpoint_uses_public_error_contract(client: TestClient) -> None:
    response = client.get("/missing")

    assert response.status_code == 404
    assert response.json() == {"message": "Endpoint not found"}


def test_unhandled_error_uses_public_error_contract(
    app: FastAPI,
    client: TestClient,
) -> None:
    @app.get("/failure")
    def fail() -> None:
        raise RuntimeError("private detail")

    response = client.get("/failure")

    assert response.status_code == 500
    assert response.json() == {"message": "Internal server error"}
