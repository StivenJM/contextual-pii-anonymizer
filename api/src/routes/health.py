from fastapi import APIRouter

from controllers.health_controller import get_health
from controllers.dtos.health_controller_dto import HealthResponse


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def read_health() -> HealthResponse:
    return get_health()
