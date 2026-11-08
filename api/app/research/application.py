"""Model-free entry point: no PostgreSQL or inference startup dependencies."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.research.router import router


def create_research_app() -> FastAPI:
    app = FastAPI(title="Research Capture API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^(chrome-extension|moz-extension)://[A-Za-z0-9_-]+$",
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Research-Key",
            "X-Research-Enrollment",
        ],
    )
    app.include_router(router)
    return app


app = create_research_app()
