import pytest
from pydantic import ValidationError

from app.config import Settings

VALID_SETTINGS = {
    "POSTGRES_HOST": "127.0.0.1",
    "POSTGRES_PORT": 5432,
    "POSTGRES_DB": "contextual_pii",
    "POSTGRES_USER": "contextual_pii",
    "POSTGRES_PASSWORD": "local-password",
}


def test_accepts_complete_database_configuration() -> None:
    settings = Settings(**VALID_SETTINGS)

    assert settings.postgres_host == "127.0.0.1"
    assert settings.postgres_port == 5432
    assert settings.postgres_db == "contextual_pii"
    assert settings.postgres_user == "contextual_pii"


def test_rejects_missing_database_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in VALID_SETTINGS:
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    "invalid",
    [
        {"POSTGRES_HOST": "   "},
        {"POSTGRES_PORT": 0},
        {"POSTGRES_PORT": 65536},
        {"POSTGRES_DB": ""},
        {"POSTGRES_USER": ""},
        {"POSTGRES_PASSWORD": ""},
    ],
)
def test_rejects_invalid_database_configuration(invalid: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        Settings(**(VALID_SETTINGS | invalid))


def test_masks_password_in_settings_representation() -> None:
    password = "not-for-logs"
    settings = Settings(**(VALID_SETTINGS | {"POSTGRES_PASSWORD": password}))

    assert password not in repr(settings)
