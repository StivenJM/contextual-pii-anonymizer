import re

from app.domain.configuration import Gazetteer
from app.domain.detections import CanonicalDetection, DetectionSource, Provenance


class GazetteerMatcher:
    def detect(self, text: str, gazetteers: list[Gazetteer]) -> list[CanonicalDetection]:
        detections: list[CanonicalDetection] = []
        for gazetteer in gazetteers:
            if not gazetteer.enabled:
                continue
            flags = 0 if gazetteer.case_sensitive else re.IGNORECASE
            for entry in gazetteer.entries:
                if not entry.value:
                    continue
                pattern = rf"(?<!\w){re.escape(entry.value)}(?!\w)"
                for match in re.finditer(pattern, text, flags):
                    detections.append(
                        CanonicalDetection(
                            canonical_type=gazetteer.canonical_type,
                            text=match.group(0),
                            start=match.start(),
                            end=match.end(),
                            confidence=gazetteer.score,
                            provenance=Provenance(
                                source=DetectionSource.GAZETTEER,
                                source_id=str(gazetteer.id or gazetteer.name),
                            ),
                        )
                    )
        return detections
