import unittest

from app.domain.configuration import ProtectionAction
from app.domain.detections import CanonicalDetection, DetectionSource, Provenance
from app.engines.deidentification import DeidentificationEngine
from app.engines.protection import ProtectionDecision
from app.engines.validators import validate_ecuador_national_id


def decision(
    entity_type: str,
    text: str,
    start: int,
    action: ProtectionAction,
) -> ProtectionDecision:
    detection = CanonicalDetection(
        entity_type,
        text,
        start,
        start + len(text),
        0.9,
        Provenance(DetectionSource.PATTERN),
    )
    return ProtectionDecision(detection, action, entity_type)


class DeidentificationEngineTests(unittest.TestCase):
    def test_applies_multiple_operations_without_destroying_offsets(self) -> None:
        text = "Juan usa juan@example.com"
        result = DeidentificationEngine().apply(
            text,
            [
                decision("PERSON_NAME", "Juan", 0, ProtectionAction.REPLACE_WITH_LABEL),
                decision("EMAIL", "juan@example.com", 9, ProtectionAction.MASK),
            ],
        )
        self.assertEqual(result.protected_text, "<PERSON_NAME> usa ****************")

    def test_reuses_pseudonym_for_same_value_in_one_interaction(self) -> None:
        text = "Juan y Juan"
        result = DeidentificationEngine().apply(
            text,
            [
                decision("PERSON_NAME", "Juan", 0, ProtectionAction.PSEUDONYMIZE),
                decision("PERSON_NAME", "Juan", 7, ProtectionAction.PSEUDONYMIZE),
            ],
        )
        parts = result.protected_text.split(" y ")
        self.assertEqual(parts[0], parts[1])

    def test_keep_and_mapping_gap_mask(self) -> None:
        result = DeidentificationEngine().apply(
            "Quito secret",
            [decision("LOCATION", "Quito", 0, ProtectionAction.KEEP)],
            [(6, 12, "secret")],
        )
        self.assertEqual(result.protected_text, "Quito ******")
        self.assertTrue(result.operations[-1].mapping_gap)

    def test_generates_compatible_national_id(self) -> None:
        result = DeidentificationEngine().apply(
            "1710034065",
            [
                decision(
                    "NATIONAL_ID",
                    "1710034065",
                    0,
                    ProtectionAction.PSEUDONYMIZE,
                )
            ],
        )
        self.assertTrue(validate_ecuador_national_id(result.protected_text))


if __name__ == "__main__":
    unittest.main()
