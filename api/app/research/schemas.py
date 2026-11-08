from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
    model_validator,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StartSession(StrictModel):
    session_id: UUID
    upload_token: str = Field(min_length=32, max_length=128)
    protocol_version: str = Field(min_length=1, max_length=80)
    consent: Literal[True]
    training_consent: StrictBool = False
    provider: Literal["chatgpt", "claude", "gemini"]

    @field_validator("consent", mode="before")
    @classmethod
    def explicit_consent(cls, value):
        if value is not True:
            raise ValueError("Explicit boolean consent is required")
        return value


class CaptureEvent(StrictModel):
    event_id: UUID
    role: Literal["user", "assistant"]
    text: str = Field(min_length=1, max_length=100_000)
    captured_at: str = Field(max_length=40)
    task_id: str = Field(default="unassigned", pattern=r"^[A-Za-z0-9_-]{1,64}$")

    @field_validator("text")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Blank text")
        return value

    @field_validator("captured_at")
    @classmethod
    def aware_timestamp(cls, value: str) -> str:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            raise ValueError("Timezone required")
        return value


class CompleteSession(StrictModel):
    schema_version: Literal[1]
    capture_status: Literal["complete", "interrupted"] = "complete"
    events: list[CaptureEvent] = Field(min_length=1, max_length=1_000)

    @model_validator(mode="after")
    def unique_events(self):
        if len({event.event_id for event in self.events}) != len(self.events):
            raise ValueError("Duplicate event ID")
        if not any(event.role == "user" for event in self.events):
            raise ValueError("A participant submission is required")
        return self
