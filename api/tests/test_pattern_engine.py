import unittest

from app.domain.configuration import PatternRecognizer
from app.engines.patterns import PatternRecognizerEngine
from app.engines.validators import validate_ecuador_national_id


class PatternRecognizerEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PatternRecognizerEngine()

    def test_detects_email_and_ecuador_phone(self) -> None:
        recognizers = [
            PatternRecognizer(None, "email", "EMAIL", (r"\b[\w.+-]+@[\w.-]+\.\w+\b",), 0.95),
            PatternRecognizer(None, "phone", "PHONE", (r"(?<!\d)09\d{8}(?!\d)",), 0.8),
        ]
        detections = self.engine.detect("Escriba a ana@example.com o llame al 0991234567", recognizers)
        self.assertEqual([item.canonical_type for item in detections], ["EMAIL", "PHONE"])

    def test_validates_ecuador_national_id(self) -> None:
        self.assertTrue(validate_ecuador_national_id("1710034065"))
        self.assertFalse(validate_ecuador_national_id("1710034064"))
        recognizer = PatternRecognizer(
            1,
            "cedula",
            "NATIONAL_ID",
            (r"(?<!\d)\d{10}(?!\d)",),
            0.88,
            ("cédula",),
            "ecuador_national_id",
        )
        detections = self.engine.detect(
            "Cédula 1710034065, dato inválido 1710034064",
            [recognizer],
        )
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0].text, "1710034065")
        self.assertEqual(detections[0].confidence, 0.98)

    def test_ignores_disabled_recognizer(self) -> None:
        recognizer = PatternRecognizer(None, "email", "EMAIL", (r".+@.+",), 0.9, enabled=False)
        self.assertEqual(self.engine.detect("a@example.com", [recognizer]), [])


if __name__ == "__main__":
    unittest.main()
