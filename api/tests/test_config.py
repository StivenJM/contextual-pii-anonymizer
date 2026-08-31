import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from app.config import Settings


VALID_SETTINGS = {
    "POSTGRES_HOST": "127.0.0.1",
    "POSTGRES_PORT": 5432,
    "POSTGRES_DB": "contextual_pii",
    "POSTGRES_USER": "contextual_pii",
    "POSTGRES_PASSWORD": "local-password",
}


class SettingsTests(unittest.TestCase):
    def test_accepts_complete_database_configuration(self) -> None:
        settings = Settings(**VALID_SETTINGS)

        self.assertEqual(settings.postgres_host, "127.0.0.1")
        self.assertEqual(settings.postgres_port, 5432)
        self.assertEqual(settings.postgres_db, "contextual_pii")
        self.assertEqual(settings.postgres_user, "contextual_pii")

    def test_rejects_missing_database_configuration(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValidationError):
                Settings()

    def test_rejects_invalid_database_configuration(self) -> None:
        invalid_values = (
            {"POSTGRES_HOST": "   "},
            {"POSTGRES_PORT": 0},
            {"POSTGRES_PORT": 65536},
            {"POSTGRES_DB": ""},
            {"POSTGRES_USER": ""},
            {"POSTGRES_PASSWORD": ""},
        )

        for invalid in invalid_values:
            with self.subTest(invalid=invalid):
                values = VALID_SETTINGS | invalid
                with self.assertRaises(ValidationError):
                    Settings(**values)

    def test_masks_password_in_settings_representation(self) -> None:
        password = "not-for-logs"
        settings = Settings(**(VALID_SETTINGS | {"POSTGRES_PASSWORD": password}))

        self.assertNotIn(password, repr(settings))


if __name__ == "__main__":
    unittest.main()
