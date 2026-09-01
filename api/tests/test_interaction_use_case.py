import unittest

from app.domain.configuration import (
    DetectionSettings,
    Gazetteer,
    GazetteerEntry,
    ModelMapping,
    PatternRecognizer,
    ProtectionAction,
    ProtectionRule,
)
from app.domain.detections import DetectionSource
from app.services.inference import NativeDetection, NativeInferenceResult
from app.use_cases.interactions import ProtectInteractionUseCase


class FakeConfigurationRepository:
    async def get_active_model_id(self) -> str:
        return "model-a"

    async def get_detection_settings(self) -> DetectionSettings:
        return DetectionSettings(threshold=0.5)

    async def list_mappings(self, _model_id: str) -> list[ModelMapping]:
        return [ModelMapping(1, "model-a", "FIRSTNAME", "PERSON_NAME")]

    async def list_patterns(self) -> list[PatternRecognizer]:
        return [
            PatternRecognizer(
                1,
                "email",
                "EMAIL",
                (r"\b[\w.+-]+@[\w.-]+\.\w+\b",),
                0.95,
            )
        ]

    async def list_gazetteers(self) -> list[Gazetteer]:
        return [
            Gazetteer(
                1,
                "universities",
                "EDUCATIONAL_AFFILIATION",
                entries=(GazetteerEntry(1, "EPN"),),
            )
        ]

    async def list_protection_rules(self) -> list[ProtectionRule]:
        return [ProtectionRule(1, "PII", ProtectionAction.REPLACE_WITH_LABEL)]


class FakeInferenceService:
    async def detect(self, _model_id: str, text: str) -> NativeInferenceResult:
        return NativeInferenceResult(
            "model-a",
            "v1",
            (
                NativeDetection("FIRSTNAME", "Juan", 0, 4, 0.9),
                NativeDetection("UNKNOWN_SECRET", "secreto", text.index("secreto"), text.index("secreto") + 7, 0.99),
            ),
        )


class ProtectInteractionUseCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_runs_all_sources_and_masks_mapping_gaps(self) -> None:
        text = "Juan estudia en EPN, escribe a juan@example.com y guarda secreto"
        result = await ProtectInteractionUseCase(
            FakeConfigurationRepository(),
            FakeInferenceService(),
        ).execute(text)

        self.assertEqual(
            {item.provenance.source for item in result.detections},
            {DetectionSource.MODEL, DetectionSource.PATTERN, DetectionSource.GAZETTEER},
        )
        self.assertEqual(result.mapping_gaps[0].native_entity_type, "UNKNOWN_SECRET")
        self.assertNotIn("secreto", result.protected_text)
        self.assertIn("<PERSON_NAME>", result.protected_text)
        self.assertTrue(result.warnings)


if __name__ == "__main__":
    unittest.main()
