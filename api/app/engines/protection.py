from dataclasses import dataclass

from app.domain.configuration import ProtectionAction, ProtectionRule
from app.domain.detections import CanonicalDetection
from app.domain.taxonomy import ancestors


@dataclass(frozen=True)
class ProtectionDecision:
    detection: CanonicalDetection
    action: ProtectionAction
    rule_type: str | None


class ProtectionRuleEvaluator:
    def evaluate(
        self,
        detections: list[CanonicalDetection],
        rules: list[ProtectionRule],
    ) -> list[ProtectionDecision]:
        by_type = {rule.canonical_type: rule for rule in rules}
        decisions: list[ProtectionDecision] = []
        for detection in detections:
            rule = next(
                (
                    by_type[entity_type]
                    for entity_type in ancestors(
                        detection.canonical_type,
                        include_self=True,
                    )
                    if entity_type in by_type
                ),
                None,
            )
            decisions.append(
                ProtectionDecision(
                    detection=detection,
                    action=rule.action if rule else ProtectionAction.MASK,
                    rule_type=rule.canonical_type if rule else None,
                )
            )
        return decisions
