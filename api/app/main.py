from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from routes import api_router

app = FastAPI(
    title="Contextual PII Anonymizer API",
    version="1.0.0",
    summary="API for contextual PII anonymization workflows.",
)

@app.get("/", tags=["root"])
def read_root() -> dict[str, str]:
    return {
        "message": "Contextual PII Anonymizer API",
        "version": "1.0.0",
        "status": "active",
    }

@app.exception_handler(404)
async def not_found_handler(
    _request: Request,
    _exc: StarletteHTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"message": "Endpoint not found"},
    )

@app.exception_handler(Exception)
async def internal_error_handler(
    _request: Request,
    _exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"},
    )

app.include_router(api_router)
