import pytest

from app.domain.configuration import PatternRecognizer
from app.engines.patterns import PatternRecognizerEngine
from app.engines.validators import validate_ecuador_national_id


@pytest.fixture
def engine() -> PatternRecognizerEngine:
    return PatternRecognizerEngine()


def test_detects_email_and_ecuador_phone(engine: PatternRecognizerEngine) -> None:
    recognizers = [
        PatternRecognizer(
            None,
            "email",
            "EMAIL",
            (r"\b[\w.+-]+@[\w.-]+\.\w+\b",),
            0.95,
        ),
        PatternRecognizer(None, "phone", "PHONE", (r"(?<!\d)09\d{8}(?!\d)",), 0.8),
    ]

    detections = engine.detect(
        "Escriba a ana@example.com o llame al 0991234567",
        recognizers,
    )

    assert [item.canonical_type for item in detections] == ["EMAIL", "PHONE"]


def test_validates_ecuador_national_id(engine: PatternRecognizerEngine) -> None:
    assert validate_ecuador_national_id("1710034065")
    assert not validate_ecuador_national_id("1710034064")
    recognizer = PatternRecognizer(
        1,
        "cedula",
        "NATIONAL_ID",
        (r"(?<!\d)\d{10}(?!\d)",),
        0.88,
        ("cédula",),
        "ecuador_national_id",
    )

    detections = engine.detect(
        "Cédula 1710034065, dato inválido 1710034064",
        [recognizer],
    )

    assert len(detections) == 1
    assert detections[0].text == "1710034065"
    assert detections[0].confidence == 0.98


def test_ignores_disabled_recognizer(engine: PatternRecognizerEngine) -> None:
    recognizer = PatternRecognizer(
        None,
        "email",
        "EMAIL",
        (r".+@.+",),
        0.9,
        enabled=False,
    )

    assert engine.detect("a@example.com", [recognizer]) == []
