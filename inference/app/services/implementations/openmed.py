from collections.abc import Callable
from typing import Any

from app.entities.detections import Detection


MODEL_ID = "OpenMed/OpenMed-PII-Spanish-QwenMed-XLarge-600M-v1"


class OpenMedModel:
    def __init__(
        self,
        pipeline: Callable[[str], list[dict[str, Any]]] | None = None,
    ) -> None:
        self.model_id = MODEL_ID
        self.pipeline = pipeline or self._load_pipeline()

    def detect(self, text: str) -> list[Detection]:
        return [self._to_detection(raw, text) for raw in self.pipeline(text)]

    def _load_pipeline(self) -> Callable[[str], list[dict[str, Any]]]:
        try:
            import torch
            from transformers import pipeline
        except ImportError as exc:
            raise RuntimeError(
                "Missing inference dependencies. Install them with: "
                "python -m pip install -e ."
            ) from exc

        device = 0 if torch.cuda.is_available() else -1

        return pipeline(
            task="token-classification",
            model=self.model_id,
            tokenizer=self.model_id,
            aggregation_strategy="simple",
            device=device,
            trust_remote_code=True,
        )

    def _to_detection(
        self,
        raw: dict[str, Any],
        source_text: str,
    ) -> Detection:
        start = int(raw["start"])
        end = int(raw["end"])

        if end > len(source_text):
            raise ValueError(f"Model returned an invalid span: [{start}, {end}).")

        return Detection(
            native_type=self._native_type(raw),
            text=source_text[start:end],
            start=start,
            end=end,
            confidence=float(raw["score"]),
        )

    def _native_type(self, raw: dict[str, Any]) -> str:
        if raw.get("entity_group"):
            return str(raw["entity_group"])

        label = str(raw["entity"])
        if label.startswith(("B-", "I-")):
            return label[2:]
        return label
