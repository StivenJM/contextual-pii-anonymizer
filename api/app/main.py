import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.lifespan import lifespan
from app.routers import router

logger = logging.getLogger(__name__)


async def not_found_handler(
    _request: Request,
    _exc: StarletteHTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"message": "Endpoint not found"},
    )

async def internal_error_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception("Unhandled API error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="Contextual PII Anonymizer API",
        version="1.0.0",
        summary="API for contextual PII anonymization workflows.",
        lifespan=lifespan,
    )
    app.add_exception_handler(404, not_found_handler)
    app.add_exception_handler(Exception, internal_error_handler)
    app.include_router(router)
    return app


app = create_app()
