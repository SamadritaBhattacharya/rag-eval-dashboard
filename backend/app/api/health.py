"""Liveness probe route."""

from __future__ import annotations

from fastapi import APIRouter

from app.models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Report that the process is up and serving requests.

    Deliberately has no dependencies — no ChromaDB read, no Groq call. It
    only proves the process itself is alive, which is what deployment
    platforms (Railway/Fly) and uptime checks need. Dependency health
    belongs in a separate, deeper check if we ever need one.
    """
    return HealthResponse(status="ok")
