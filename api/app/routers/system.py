from fastapi import APIRouter

from app.schemas.system import HealthResponse, RootResponse


router = APIRouter(tags=["system"])


@router.get("/", response_model=RootResponse)
def read_root() -> RootResponse:
    return RootResponse(
        message="Contextual PII Anonymizer API",
        version="1.0.0",
        status="active",
    )


@router.get("/api/health", response_model=HealthResponse)
def read_health() -> HealthResponse:
    return HealthResponse(
        message="Contextual PII Anonymizer API",
        version="1.0.0",
        status="active",
    )
