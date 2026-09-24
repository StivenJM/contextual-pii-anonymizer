import pytest

from app.domain.configuration import ProtectionAction, ProtectionRule
from app.domain.detections import CanonicalDetection, DetectionSource, Provenance
from app.engines.protection import ProtectionRuleEvaluator


def item(entity_type: str) -> CanonicalDetection:
    return CanonicalDetection(
        entity_type,
        "value",
        0,
        5,
        0.9,
        Provenance(DetectionSource.PATTERN),
    )


def test_parent_rule_applies_and_child_overrides() -> None:
    rules = [
        ProtectionRule(1, "IDENTIFIER", ProtectionAction.MASK),
        ProtectionRule(2, "STUDENT_ID", ProtectionAction.PSEUDONYMIZE),
    ]

    decisions = ProtectionRuleEvaluator().evaluate(
        [item("NATIONAL_ID"), item("STUDENT_ID")],
        rules,
    )

    assert [decision.action for decision in decisions] == [
        ProtectionAction.MASK,
        ProtectionAction.PSEUDONYMIZE,
    ]


@pytest.mark.parametrize("action", list(ProtectionAction))
def test_supports_each_protection_action(action: ProtectionAction) -> None:
    decision = ProtectionRuleEvaluator().evaluate(
        [item("EMAIL")],
        [ProtectionRule(1, "EMAIL", action)],
    )[0]

    assert decision.action == action


def test_missing_rule_uses_safe_mask_default() -> None:
    decision = ProtectionRuleEvaluator().evaluate([item("EMAIL")], [])[0]

    assert decision.action == ProtectionAction.MASK
