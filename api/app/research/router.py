import json
import os
import secrets
import sqlite3
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, ValidationError
from starlette.concurrency import run_in_threadpool

from app.research.errors import ResearchError
from app.research.schemas import CompleteSession, StartSession
from app.research.storage import CaptureStore

MAX_BODY_BYTES = 1_000_000


def documented_body(model: type[BaseModel]) -> dict:
    """Expose the same bounded model despite manually streaming the request.

    Inline local definitions so request-body references remain valid inside
    both the standalone and ordinary application's OpenAPI documents.
    """
    schema = model.model_json_schema()
    definitions = schema.pop("$defs", {})

    def inline(value):
        if isinstance(value, list):
            return [inline(item) for item in value]
        if isinstance(value, dict):
            if "$ref" in value:
                return inline(definitions[value["$ref"].split("/")[-1]])
            return {key: inline(item) for key, item in value.items()}
        return value

    return {
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": inline(schema)}},
        }
    }


def secret_value(name: str) -> str:
    value = os.getenv(name, "")
    filename = os.getenv(name + "_FILE", "")
    if filename:
        if value or not Path(filename).is_absolute():
            raise ValueError("Invalid secret source")
        with Path(filename).open("rb") as stream:
            raw = stream.read(4099)
        if len(raw) > 4098:
            raise ValueError("Invalid secret size")
        value = raw.decode("utf-8").rstrip("\r\n")
    if value and not 32 <= len(value.encode("utf-8")) <= 4096:
        raise ValueError("Invalid secret size")
    return value


def configuration() -> dict:
    if os.getenv("RESEARCH_ENABLED", "false").lower() != "true":
        raise HTTPException(404, "Research capture is disabled")
    path = Path(os.getenv("RESEARCH_STORAGE_PATH", ""))
    try:
        key = secret_value("RESEARCH_API_KEY")
        enrollment = secret_value("RESEARCH_ENROLLMENT_KEY")
        require_enrollment = os.getenv("RESEARCH_REQUIRE_ENROLLMENT", "false").lower()
        if require_enrollment not in ("true", "false"):
            raise ValueError("Invalid enrollment mode")
        if enrollment and secrets.compare_digest(enrollment.encode(), key.encode()):
            raise ValueError("Enrollment must be distinct")
        if require_enrollment == "true" and not enrollment:
            raise ValueError("Enrollment is required")
        days = int(os.getenv("RESEARCH_RETENTION_DAYS", "30"))
    except ValueError, OSError, UnicodeError:
        raise HTTPException(503, "Research configuration is incomplete") from None
    if not key or not path.is_absolute() or not 1 <= days <= 365:
        raise HTTPException(503, "Research configuration is incomplete")
    return {
        "key": key,
        "enrollment": enrollment,
        "require_enrollment": require_enrollment == "true",
        "path": path,
        "days": days,
        "protocol": os.getenv("RESEARCH_PROTOCOL_VERSION", "research-v1"),
    }


Config = Annotated[dict, Depends(configuration)]


def researcher(config: Config, x_research_key: Annotated[str, Header()] = "") -> dict:
    if not secrets.compare_digest(x_research_key.encode(), config["key"].encode()):
        raise HTTPException(401, "Research authorization required")
    return config


def participant(
    config: Config,
    x_research_enrollment: Annotated[str, Header()] = "",
    x_research_key: Annotated[str, Header()] = "",
) -> dict:
    if config["enrollment"] and secrets.compare_digest(
        x_research_enrollment.encode(), config["enrollment"].encode()
    ):
        return config
    if not config["require_enrollment"] and secrets.compare_digest(
        x_research_key.encode(), config["key"].encode()
    ):
        return config
    raise HTTPException(401, "Research enrollment required")


def capability(authorization: Annotated[str, Header()] = "") -> str:
    if not authorization.startswith("Bearer ") or len(authorization) > 136:
        raise HTTPException(404, "Session unavailable")
    return authorization[7:]


async def read_body(request: Request, schema):
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        raise HTTPException(415, "JSON required")
    buffer = bytearray()
    async for chunk in request.stream():
        buffer.extend(chunk)
        if len(buffer) > MAX_BODY_BYTES:
            raise HTTPException(413, "Research upload exceeds limit")
    try:
        return schema.model_validate_json(buffer)
    except ValidationError, ValueError, json.JSONDecodeError:
        # Never echo a participant's text in validation errors.
        raise HTTPException(422, "Invalid research payload") from None


async def execute(config: dict, operation: str, *args):
    def perform():
        store = CaptureStore(config["path"], config["days"])
        return getattr(store, operation)(*args)

    try:
        return await run_in_threadpool(perform)
    except ResearchError as error:
        raise HTTPException(error.status_code, error.detail) from None
    except sqlite3.Error, OSError:
        raise HTTPException(
            503, "Research storage unavailable; retain the local copy"
        ) from None


router = APIRouter(
    prefix="/api/research", tags=["research"], dependencies=[Depends(configuration)]
)


@router.get("/health")
async def health(config: Config):
    await execute(config, "check")
    return {"status": "ready"}


@router.post("/sessions", status_code=201, openapi_extra=documented_body(StartSession))
async def start_session(
    request: Request, config: Annotated[dict, Depends(participant)]
):
    body = await read_body(request, StartSession)
    if body.protocol_version != config["protocol"]:
        raise HTTPException(409, "Protocol version mismatch")
    return await execute(config, "start", body)


@router.put(
    "/sessions/{session_id}/complete", openapi_extra=documented_body(CompleteSession)
)
async def complete_session(
    session_id: UUID,
    request: Request,
    config: Config,
    token: Annotated[str, Depends(capability)],
):
    body = await read_body(request, CompleteSession)
    return await execute(config, "complete", str(session_id), token, body)


@router.get("/records/{receipt_id}")
async def export_record(
    receipt_id: str, config: Annotated[dict, Depends(researcher)], response: Response
):
    response.headers["Cache-Control"] = "no-store"
    return await execute(config, "export", receipt_id)


@router.delete("/sessions/{session_id}", status_code=204)
async def withdraw_session(
    session_id: UUID, config: Config, token: Annotated[str, Depends(capability)]
):
    await execute(config, "withdraw", str(session_id), token)
    return Response(status_code=204)


@router.post("/purge-expired")
async def purge_expired(config: Annotated[dict, Depends(researcher)]):
    return {"deleted": await execute(config, "purge_expired")}


@router.delete("/records/{receipt_id}", status_code=204)
async def withdraw_record(
    receipt_id: str, config: Annotated[dict, Depends(researcher)]
):
    await execute(config, "withdraw_record", receipt_id)
    return Response(status_code=204)
