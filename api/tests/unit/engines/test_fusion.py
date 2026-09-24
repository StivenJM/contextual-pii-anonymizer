import pytest

from app.domain.configuration import DetectionSettings
from app.domain.detections import CanonicalDetection, DetectionSource, Provenance
from app.engines.fusion import DetectionFusion


def detection(
    entity_type: str,
    start: int,
    end: int,
    source: DetectionSource,
    confidence: float = 0.9,
) -> CanonicalDetection:
    return CanonicalDetection(
        entity_type,
        "x" * (end - start),
        start,
        end,
        confidence,
        Provenance(source),
    )


@pytest.fixture
def fusion() -> DetectionFusion:
    return DetectionFusion()


@pytest.fixture
def settings() -> DetectionSettings:
    return DetectionSettings()


def test_exact_parent_child_prefers_specific_category(
    fusion: DetectionFusion,
    settings: DetectionSettings,
) -> None:
    result = fusion.fuse(
        [
            detection("IDENTIFIER", 0, 10, DetectionSource.MODEL, 0.99),
            detection("NATIONAL_ID", 0, 10, DetectionSource.PATTERN, 0.8),
        ],
        settings,
    )

    assert [item.canonical_type for item in result] == ["NATIONAL_ID"]


def test_deduplicates_same_type_and_span_by_priority(
    fusion: DetectionFusion,
    settings: DetectionSettings,
) -> None:
    result = fusion.fuse(
        [
            detection("EMAIL", 0, 5, DetectionSource.MODEL, 0.99),
            detection("EMAIL", 0, 5, DetectionSource.PATTERN, 0.7),
        ],
        settings,
    )

    assert result[0].provenance.source == DetectionSource.PATTERN


def test_same_span_incompatible_uses_priority_then_confidence(
    fusion: DetectionFusion,
    settings: DetectionSettings,
) -> None:
    result = fusion.fuse(
        [
            detection("EMAIL", 0, 5, DetectionSource.MODEL, 0.99),
            detection("PHONE", 0, 5, DetectionSource.GAZETTEER, 0.6),
        ],
        settings,
    )

    assert result[0].canonical_type == "PHONE"


def test_resolves_partial_overlap_without_returning_overlap(
    fusion: DetectionFusion,
    settings: DetectionSettings,
) -> None:
    result = fusion.fuse(
        [
            detection("PERSON_NAME", 0, 10, DetectionSource.MODEL, 0.9),
            detection("EMAIL", 5, 15, DetectionSource.PATTERN, 0.8),
            detection("USERNAME", 6, 9, DetectionSource.MODEL, 1.0),
        ],
        settings,
    )

    assert [(item.start, item.end) for item in result] == [(5, 15)]


def test_respects_confidence_after_equal_priority(
    fusion: DetectionFusion,
    settings: DetectionSettings,
) -> None:
    result = fusion.fuse(
        [
            detection("EMAIL", 0, 8, DetectionSource.MODEL, 0.8),
            detection("PHONE", 2, 9, DetectionSource.MODEL, 0.9),
        ],
        settings,
    )

    assert result[0].canonical_type == "PHONE"


def test_filters_threshold_and_disabled_sources(fusion: DetectionFusion) -> None:
    settings = DetectionSettings(threshold=0.8, model_enabled=False)
    result = fusion.fuse(
        [
            detection("EMAIL", 0, 5, DetectionSource.PATTERN, 0.7),
            detection("PHONE", 6, 11, DetectionSource.MODEL, 0.99),
        ],
        settings,
    )

    assert result == []
