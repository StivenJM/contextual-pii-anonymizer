from fastapi import APIRouter

from app.routers.administration import router as administration_router
from app.routers.interactions import router as interactions_router
from app.routers.system import router as system_router


router = APIRouter()
router.include_router(system_router)
router.include_router(administration_router)
router.include_router(interactions_router)
