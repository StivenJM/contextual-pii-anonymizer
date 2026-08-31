import unittest

from pydantic import ValidationError

from app.schemas.inference import InferenceRequest


class InferenceRequestTests(unittest.TestCase):
    def test_rejects_empty_and_whitespace_only_text(self) -> None:
        for text in ("", "   "):
            with self.subTest(text=text):
                with self.assertRaises(ValidationError):
                    InferenceRequest(model_id="model-a", text=text)

    def test_rejects_non_string_text(self) -> None:
        with self.assertRaises(ValidationError):
            InferenceRequest(model_id="model-a", text=123)  # type: ignore[arg-type]

    def test_requires_a_non_blank_logical_model_id(self) -> None:
        for model_id in ("", "   "):
            with self.subTest(model_id=model_id):
                with self.assertRaises(ValidationError):
                    InferenceRequest(model_id=model_id, text="Juan")


if __name__ == "__main__":
    unittest.main()
