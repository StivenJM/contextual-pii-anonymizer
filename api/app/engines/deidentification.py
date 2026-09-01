from dataclasses import dataclass
import hashlib

from app.domain.configuration import ProtectionAction
from app.engines.protection import ProtectionDecision


@dataclass(frozen=True)
class AppliedOperation:
    canonical_type: str | None
    start: int
    end: int
    original_text: str
    replacement: str
    action: ProtectionAction
    mapping_gap: bool = False


@dataclass(frozen=True)
class DeidentificationResult:
    protected_text: str
    operations: tuple[AppliedOperation, ...]


class DeidentificationEngine:
    _NAMES = ("Andrea Molina", "Carlos Vega", "Elena Torres", "Mateo Silva")

    def apply(
        self,
        text: str,
        decisions: list[ProtectionDecision],
        gap_spans: list[tuple[int, int, str]] | None = None,
    ) -> DeidentificationResult:
        replacements: dict[tuple[str, str], str] = {}
        operations: list[AppliedOperation] = []
        occupied: list[tuple[int, int]] = []

        for decision in decisions:
            detection = decision.detection
            replacement = self._replacement(
                decision.action,
                detection.canonical_type,
                detection.text,
                replacements,
            )
            operations.append(
                AppliedOperation(
                    canonical_type=detection.canonical_type,
                    start=detection.start,
                    end=detection.end,
                    original_text=detection.text,
                    replacement=replacement,
                    action=decision.action,
                )
            )
            occupied.append((detection.start, detection.end))

        for start, end, value in gap_spans or []:
            if any(start < used_end and used_start < end for used_start, used_end in occupied):
                continue
            operations.append(
                AppliedOperation(
                    canonical_type=None,
                    start=start,
                    end=end,
                    original_text=value,
                    replacement="*" * max(4, len(value)),
                    action=ProtectionAction.MASK,
                    mapping_gap=True,
                )
            )
            occupied.append((start, end))

        protected = text
        for operation in sorted(operations, key=lambda item: item.start, reverse=True):
            protected = protected[: operation.start] + operation.replacement + protected[operation.end :]
        return DeidentificationResult(
            protected_text=protected,
            operations=tuple(sorted(operations, key=lambda item: item.start)),
        )

    def _replacement(
        self,
        action: ProtectionAction,
        canonical_type: str,
        value: str,
        cache: dict[tuple[str, str], str],
    ) -> str:
        if action == ProtectionAction.KEEP:
            return value
        if action == ProtectionAction.MASK:
            return "*" * max(4, len(value))
        if action == ProtectionAction.REPLACE_WITH_LABEL:
            return f"<{canonical_type}>"

        key = (canonical_type, value.casefold())
        if key not in cache:
            cache[key] = self._pseudonym(canonical_type, value)
        return cache[key]

    def _pseudonym(self, canonical_type: str, value: str) -> str:
        digest = int(hashlib.sha256(f"{canonical_type}:{value}".encode()).hexdigest()[:8], 16)
        if canonical_type == "PERSON_NAME":
            return self._NAMES[digest % len(self._NAMES)]
        if canonical_type == "EMAIL":
            return f"persona{digest % 10000:04d}@example.org"
        if canonical_type == "PHONE":
            return f"09{digest % 100000000:08d}"
        if canonical_type == "NATIONAL_ID":
            base = f"17{(digest // 1000000) % 6}{digest % 1000000:06d}"
            total = sum(
                ((int(character) * (2 if index % 2 == 0 else 1)) - 9)
                if int(character) * (2 if index % 2 == 0 else 1) > 9
                else int(character) * (2 if index % 2 == 0 else 1)
                for index, character in enumerate(base)
            )
            return base + str((10 - total % 10) % 10)
        if canonical_type == "STUDENT_ID":
            return f"STU-{digest % 1000000:06d}"
        if canonical_type == "USERNAME":
            return f"usuario_{digest % 10000:04d}"
        return f"SYNTHETIC_{canonical_type}_{digest % 10000:04d}"
