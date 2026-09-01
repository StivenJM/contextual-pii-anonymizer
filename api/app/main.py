import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import (
    InferenceUnavailableError,
    InvalidConfigurationError,
    ModelUnavailableError,
    ResourceNotFoundError,
)
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


async def application_error_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    if isinstance(exc, (ResourceNotFoundError, ModelUnavailableError)):
        status_code = 404
    elif isinstance(exc, InferenceUnavailableError):
        status_code = 502
    elif isinstance(exc, IntegrityError):
        status_code = 409
    else:
        status_code = 400
    return JSONResponse(status_code=status_code, content={"message": str(exc)})


def create_app() -> FastAPI:
    app = FastAPI(
        title="Contextual PII Anonymizer API",
        version="1.0.0",
        summary="API for contextual PII anonymization workflows.",
        lifespan=lifespan,
    )
    app.add_exception_handler(404, not_found_handler)
    app.add_exception_handler(ResourceNotFoundError, application_error_handler)
    app.add_exception_handler(ModelUnavailableError, application_error_handler)
    app.add_exception_handler(InferenceUnavailableError, application_error_handler)
    app.add_exception_handler(InvalidConfigurationError, application_error_handler)
    app.add_exception_handler(ValueError, application_error_handler)
    app.add_exception_handler(IntegrityError, application_error_handler)
    app.add_exception_handler(Exception, internal_error_handler)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
        allow_origin_regex=r"^(chrome-extension|moz-extension)://.*$",
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
