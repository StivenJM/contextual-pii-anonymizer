import unittest

from pydantic import ValidationError

from app.schemas.inference import InferenceRequest


class InferenceRequestTests(unittest.TestCase):
    def test_rejects_empty_and_whitespace_only_text(self) -> None:
        for text in ("", "   "):
            with self.subTest(text=text):
                with self.assertRaises(ValidationError):
                    InferenceRequest(text=text)

    def test_rejects_non_string_text(self) -> None:
        with self.assertRaises(ValidationError):
            InferenceRequest(text=123)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
