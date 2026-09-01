import unittest

from app.domain.configuration import ProtectionAction, ProtectionRule
from app.domain.detections import CanonicalDetection, DetectionSource, Provenance
from app.engines.protection import ProtectionRuleEvaluator


def item(entity_type: str) -> CanonicalDetection:
    return CanonicalDetection(entity_type, "value", 0, 5, 0.9, Provenance(DetectionSource.PATTERN))


class ProtectionRuleEvaluatorTests(unittest.TestCase):
    def test_parent_rule_applies_and_child_overrides(self) -> None:
        rules = [
            ProtectionRule(1, "IDENTIFIER", ProtectionAction.MASK),
            ProtectionRule(2, "STUDENT_ID", ProtectionAction.PSEUDONYMIZE),
        ]
        decisions = ProtectionRuleEvaluator().evaluate(
            [item("NATIONAL_ID"), item("STUDENT_ID")],
            rules,
        )
        self.assertEqual(
            [decision.action for decision in decisions],
            [ProtectionAction.MASK, ProtectionAction.PSEUDONYMIZE],
        )

    def test_supports_all_actions_and_safe_missing_rule_default(self) -> None:
        for action in ProtectionAction:
            decision = ProtectionRuleEvaluator().evaluate(
                [item("EMAIL")],
                [ProtectionRule(1, "EMAIL", action)],
            )[0]
            self.assertEqual(decision.action, action)
        default = ProtectionRuleEvaluator().evaluate([item("EMAIL")], [])[0]
        self.assertEqual(default.action, ProtectionAction.MASK)


if __name__ == "__main__":
    unittest.main()
