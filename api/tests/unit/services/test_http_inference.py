import json

import httpx
import pytest

from app.errors import InferenceUnavailableError, ModelUnavailableError
from app.services.http_inference import HttpInferenceService

pytestmark = pytest.mark.anyio


async def test_discovers_models_and_executes_native_inference() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/models":
            return httpx.Response(
                200,
                json={
                    "models": [
                        {
                            "id": "model-a",
                            "name": "Model A",
                            "version": "v1",
                            "description": "test",
                            "native_entity_types": ["EMAIL"],
                        }
                    ]
                },
            )

        assert json.loads(request.content) == {
            "model_id": "model-a",
            "text": "a@b.com",
        }
        return httpx.Response(
            200,
            json={
                "model_id": "model-a",
                "model_version": "v1",
                "detections": [
                    {
                        "native_type": "EMAIL",
                        "text": "a@b.com",
                        "start": 0,
                        "end": 7,
                        "confidence": 0.9,
                    }
                ],
            },
        )

    async with httpx.AsyncClient(
        base_url="http://inference",
        transport=httpx.MockTransport(handler),
    ) as client:
        service = HttpInferenceService(client)
        models = await service.list_models()
        result = await service.detect("model-a", "a@b.com")

    assert models[0].id == "model-a"
    assert result.detections[0].native_type == "EMAIL"


async def test_reports_missing_model() -> None:
    async with httpx.AsyncClient(
        base_url="http://inference",
        transport=httpx.MockTransport(lambda _request: httpx.Response(404, json={})),
    ) as client:
        with pytest.raises(ModelUnavailableError):
            await HttpInferenceService(client).detect("missing", "text")


async def test_reports_inference_service_unavailability() -> None:
    def unavailable(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline")

    async with httpx.AsyncClient(
        base_url="http://inference",
        transport=httpx.MockTransport(unavailable),
    ) as client:
        with pytest.raises(InferenceUnavailableError):
            await HttpInferenceService(client).list_models()
