from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.use_cases import get_protect_interaction_use_case
from app.schemas.interactions import ProtectInteractionRequest, ProtectInteractionResponse
from app.use_cases.interactions import ProtectInteractionUseCase


router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.post("/protect", response_model=ProtectInteractionResponse)
async def protect_interaction(
    body: ProtectInteractionRequest,
    use_case: Annotated[
        ProtectInteractionUseCase,
        Depends(get_protect_interaction_use_case),
    ],
) -> ProtectInteractionResponse:
    result = await use_case.execute(body.text)
    return ProtectInteractionResponse.model_validate(asdict(result))
