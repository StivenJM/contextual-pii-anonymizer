from app.domain.configuration import Gazetteer, GazetteerEntry
from app.engines.gazetteers import GazetteerMatcher


def test_matches_entries_with_offsets_and_no_partial_words() -> None:
    gazetteer = Gazetteer(
        1,
        "universities",
        "EDUCATIONAL_AFFILIATION",
        entries=(GazetteerEntry(1, "EPN"),),
    )
    text = "Estudio en EPN, no en EPNvirtual."

    detections = GazetteerMatcher().detect(text, [gazetteer])

    assert len(detections) == 1
    assert (detections[0].start, detections[0].end) == (11, 14)


def test_ignores_disabled_gazetteer() -> None:
    gazetteer = Gazetteer(
        1,
        "disabled",
        "LOCATION",
        enabled=False,
        entries=(GazetteerEntry(1, "Quito"),),
    )

    assert GazetteerMatcher().detect("Quito", [gazetteer]) == []
