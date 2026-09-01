import os
import unittest

from fastapi.testclient import TestClient

from app.dependencies.services import get_inference_service
from app.main import create_app
from app.runtime import create_selector_event_loop
from app.services.inference import (
    ModelMetadata,
    NativeDetection,
    NativeInferenceResult,
)


class FakeInferenceService:
    model = ModelMetadata(
        "openmed-pii-spanish-600m",
        "OpenMed PII Spanish 600M",
        "v1",
        "Integration fake preserving the BentoML contract.",
        ("FIRSTNAME", "EMAIL", "URL", "UNKNOWN_SECRET"),
    )

    async def list_models(self) -> list[ModelMetadata]:
        return [self.model]

    async def get_model(self, model_id: str) -> ModelMetadata:
        if model_id != self.model.id:
            raise LookupError(model_id)
        return self.model

    async def detect(self, model_id: str, text: str) -> NativeInferenceResult:
        detections = [NativeDetection("FIRSTNAME", "Juan", 0, 4, 0.92)]
        if "secreto" in text:
            start = text.index("secreto")
            detections.append(
                NativeDetection("UNKNOWN_SECRET", "secreto", start, start + 7, 0.99)
            )
        return NativeInferenceResult(model_id, "v1", tuple(detections))


@unittest.skipUnless(
    os.getenv("RUN_DATABASE_INTEGRATION") == "1",
    "Set RUN_DATABASE_INTEGRATION=1 to verify privacy persistence and APIs.",
)
class PrivacyIntegrationTests(unittest.TestCase):
    def test_admin_crud_and_interaction_pipeline_use_real_postgresql(self) -> None:
        app = create_app()
        app.dependency_overrides[get_inference_service] = lambda: FakeInferenceService()
        created_mapping: int | None = None
        created_pattern: int | None = None
        created_gazetteer: int | None = None
        created_rule: int | None = None

        with TestClient(
            app,
            backend_options={"loop_factory": create_selector_event_loop},
        ) as client:
            self.assertEqual(client.get("/api/admin/taxonomy").status_code, 200)
            self.assertEqual(client.get("/api/admin/models").status_code, 200)
            active = client.get("/api/admin/models/active")
            self.assertEqual(active.status_code, 200)
            self.assertEqual(active.json()["id"], "openmed-pii-spanish-600m")

            mapping = client.post(
                "/api/admin/models/openmed-pii-spanish-600m/mappings",
                json={"native_entity_type": "URL", "canonical_type": "PERSONAL_URL"},
            )
            self.assertEqual(mapping.status_code, 201, mapping.text)
            created_mapping = mapping.json()["id"]

            pattern = client.post(
                "/api/admin/patterns",
                json={
                    "name": "Integration student ID",
                    "canonical_type": "STUDENT_ID",
                    "patterns": ["STU-[0-9]{4}"],
                    "score": 0.9,
                    "context_words": [],
                    "enabled": True,
                },
            )
            self.assertEqual(pattern.status_code, 201, pattern.text)
            created_pattern = pattern.json()["id"]
            disabled = client.patch(
                f"/api/admin/patterns/{created_pattern}/enabled",
                json={"enabled": False},
            )
            self.assertFalse(disabled.json()["enabled"])

            gazetteer = client.post(
                "/api/admin/gazetteers",
                json={
                    "name": "Integration universities",
                    "canonical_type": "EDUCATIONAL_AFFILIATION",
                    "score": 0.9,
                    "case_sensitive": False,
                    "enabled": True,
                },
            )
            self.assertEqual(gazetteer.status_code, 201, gazetteer.text)
            created_gazetteer = gazetteer.json()["id"]
            entry = client.post(
                f"/api/admin/gazetteers/{created_gazetteer}/entries",
                json={"value": "EPN"},
            )
            self.assertEqual(entry.status_code, 201, entry.text)

            rule = client.post(
                "/api/admin/protection-rules",
                json={"canonical_type": "LOCATION", "action": "KEEP"},
            )
            self.assertEqual(rule.status_code, 201, rule.text)
            created_rule = rule.json()["id"]

            settings = client.get("/api/admin/detection-settings")
            self.assertEqual(settings.status_code, 200)
            self.assertEqual(
                client.put("/api/admin/detection-settings", json=settings.json()).status_code,
                200,
            )

            protected = client.post(
                "/api/interactions/protect",
                json={
                    "text": "Juan estudia en EPN, escribe a juan@example.com con cédula 1710034065 y guarda secreto"
                },
            )
            self.assertEqual(protected.status_code, 200, protected.text)
            body = protected.json()
            self.assertNotEqual(body["original_text"], body["protected_text"])
            self.assertEqual(
                {item["provenance"]["source"] for item in body["detections"]},
                {"MODEL", "PATTERN", "GAZETTEER"},
            )
            self.assertEqual(body["mapping_gaps"][0]["native_entity_type"], "UNKNOWN_SECRET")
            self.assertNotIn("secreto", body["protected_text"])

            if created_mapping:
                self.assertEqual(client.delete(f"/api/admin/mappings/{created_mapping}").status_code, 204)
            if created_pattern:
                self.assertEqual(client.delete(f"/api/admin/patterns/{created_pattern}").status_code, 204)
            if created_gazetteer:
                self.assertEqual(client.delete(f"/api/admin/gazetteers/{created_gazetteer}").status_code, 204)
            if created_rule:
                self.assertEqual(client.delete(f"/api/admin/protection-rules/{created_rule}").status_code, 204)


if __name__ == "__main__":
    unittest.main()
