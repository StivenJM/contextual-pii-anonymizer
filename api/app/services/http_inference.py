import httpx

from app.errors import InferenceUnavailableError, ModelUnavailableError
from app.services.inference import (
    ModelMetadata,
    NativeDetection,
    NativeInferenceResult,
)


class HttpInferenceService:
    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def list_models(self) -> list[ModelMetadata]:
        data = await self._request("POST", "/models", json={})
        try:
            return [self._metadata(item) for item in data["models"]]
        except (KeyError, TypeError, ValueError) as exc:
            raise InferenceUnavailableError("BentoML returned invalid model metadata.") from exc

    async def get_model(self, model_id: str) -> ModelMetadata:
        models = await self.list_models()
        for model in models:
            if model.id == model_id:
                return model
        raise ModelUnavailableError(f"Model '{model_id}' is not available.")

    async def detect(self, model_id: str, text: str) -> NativeInferenceResult:
        data = await self._request(
            "POST",
            "/detect",
            json={"model_id": model_id, "text": text},
            model_id=model_id,
        )
        try:
            return NativeInferenceResult(
                model_id=str(data["model_id"]),
                model_version=str(data["model_version"]),
                detections=tuple(
                    NativeDetection(
                        native_type=str(item["native_type"]),
                        text=str(item["text"]),
                        start=int(item["start"]),
                        end=int(item["end"]),
                        confidence=float(item["confidence"]),
                    )
                    for item in data["detections"]
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise InferenceUnavailableError("BentoML returned an invalid inference response.") from exc

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, object],
        model_id: str | None = None,
    ) -> dict[str, object]:
        try:
            response = await self._client.request(method, path, json=json)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise InferenceUnavailableError("BentoML is unavailable.") from exc
        if response.status_code == 404 and model_id:
            raise ModelUnavailableError(f"Model '{model_id}' is not available.")
        try:
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise InferenceUnavailableError(
                f"BentoML request failed with status {response.status_code}."
            ) from exc
        if not isinstance(payload, dict):
            raise InferenceUnavailableError("BentoML returned an invalid JSON response.")
        return payload

    @staticmethod
    def _metadata(item: object) -> ModelMetadata:
        if not isinstance(item, dict):
            raise ValueError("Invalid model metadata")
        return ModelMetadata(
            id=str(item["id"]),
            name=str(item["name"]),
            version=str(item["version"]),
            description=str(item["description"]),
            native_entity_types=tuple(str(value) for value in item["native_entity_types"]),
        )
