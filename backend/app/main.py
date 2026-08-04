"""FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import health
from app.core.errors import AppError
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    """Build and configure the FastAPI application.

    Kept as a factory — rather than a bare module-level `FastAPI()` — so
    tests can construct fresh, isolated app instances (see
    `tests/api/test_errors_middleware.py`), and so logging is configured
    before any route can possibly run.
    """
    configure_logging()

    app = FastAPI(title="RAG Eval Dashboard API", version="0.1.0")

    app.include_router(health.router)

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        """Translate any `AppError` subclass into a clean JSON response.

        Anything NOT a subclass of `AppError` is deliberately left
        unhandled here — it propagates to FastAPI's default handling,
        gets logged with a full traceback, and surfaces as a plain 500.
        Only errors we anticipated get this friendly translation; genuine
        bugs stay loud.
        """
        logger.warning(
            "request_failed",
            error_type=type(exc).__name__,
            status_code=exc.status_code,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": type(exc).__name__, "message": exc.message},
        )

    return app


app = create_app()
