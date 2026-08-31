from typing import Annotated

from pydantic import Field, SecretStr, StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict


RequiredText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, extra="ignore")

    postgres_host: RequiredText = Field(validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(
        validation_alias="POSTGRES_PORT",
        ge=1,
        le=65535,
    )
    postgres_db: RequiredText = Field(validation_alias="POSTGRES_DB")
    postgres_user: RequiredText = Field(validation_alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(
        validation_alias="POSTGRES_PASSWORD",
        min_length=1,
    )
