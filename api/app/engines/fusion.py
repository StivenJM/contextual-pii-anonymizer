from app.domain.configuration import DetectionSettings
from app.domain.detections import CanonicalDetection
from app.domain.taxonomy import depth, is_a


class DetectionFusion:
    def fuse(
        self,
        detections: list[CanonicalDetection],
        settings: DetectionSettings,
    ) -> list[CanonicalDetection]:
        priority = {
            source: len(settings.source_priority) - index
            for index, source in enumerate(settings.source_priority)
        }
        candidates = [
            detection
            for detection in detections
            if detection.confidence >= settings.threshold
            and detection.provenance.source in settings.enabled_sources()
        ]

        exact_groups: dict[tuple[int, int], list[CanonicalDetection]] = {}
        for detection in candidates:
            exact_groups.setdefault((detection.start, detection.end), []).append(detection)

        reduced: list[CanonicalDetection] = []
        for group in exact_groups.values():
            reduced.append(self._select_exact(group, priority))

        ranked = sorted(
            reduced,
            key=lambda item: (
                -priority.get(item.provenance.source, 0),
                -item.confidence,
                -depth(item.canonical_type),
                -(item.end - item.start),
                item.start,
                item.canonical_type,
            ),
        )
        selected: list[CanonicalDetection] = []
        for candidate in ranked:
            if not any(self._overlaps(candidate, current) for current in selected):
                selected.append(candidate)
        return sorted(selected, key=lambda item: (item.start, item.end, item.canonical_type))

    @staticmethod
    def _select_exact(
        group: list[CanonicalDetection],
        priority: dict[object, int],
    ) -> CanonicalDetection:
        compatible = all(
            is_a(left.canonical_type, right.canonical_type)
            or is_a(right.canonical_type, left.canonical_type)
            for left in group
            for right in group
        )
        return max(
            group,
            key=lambda item: (
                depth(item.canonical_type) if compatible else 0,
                priority.get(item.provenance.source, 0),
                item.confidence,
                item.canonical_type,
            ),
        )

    @staticmethod
    def _overlaps(left: CanonicalDetection, right: CanonicalDetection) -> bool:
        return left.start < right.end and right.start < left.end
