import json
import unittest

import httpx

from app.errors import InferenceUnavailableError, ModelUnavailableError
from app.services.http_inference import HttpInferenceService


class HttpInferenceServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_discovers_models_and_executes_native_inference(self) -> None:
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
            self.assertEqual(json.loads(request.content), {"model_id": "model-a", "text": "a@b.com"})
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

        self.assertEqual(models[0].id, "model-a")
        self.assertEqual(result.detections[0].native_type, "EMAIL")

    async def test_reports_model_and_bento_unavailability(self) -> None:
        async with httpx.AsyncClient(
            base_url="http://inference",
            transport=httpx.MockTransport(lambda _request: httpx.Response(404, json={})),
        ) as client:
            with self.assertRaises(ModelUnavailableError):
                await HttpInferenceService(client).detect("missing", "text")

        def unavailable(_request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("offline")

        async with httpx.AsyncClient(
            base_url="http://inference",
            transport=httpx.MockTransport(unavailable),
        ) as client:
            with self.assertRaises(InferenceUnavailableError):
                await HttpInferenceService(client).list_models()


if __name__ == "__main__":
    unittest.main()
