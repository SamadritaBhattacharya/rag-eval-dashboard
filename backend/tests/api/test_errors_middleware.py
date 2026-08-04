"""Integration tests for the AppError -> JSON exception-handler middleware.

Each test mounts a throwaway route on a fresh app instance so we can force
a specific failure without needing a real service that raises errors yet.
"""

from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from app.core.errors import RetrievalError
from app.main import create_app


async def test_app_error_is_translated_to_clean_json_response() -> None:
    """Happy path: a known AppError subclass becomes structured JSON at
    its declared status_code, not a generic 500 page."""
    app = create_app()

    @app.get("/_boom")
    async def boom() -> None:
        raise RetrievalError("index unavailable")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/_boom")

    assert response.status_code == 500
    assert response.json() == {
        "error": "RetrievalError",
        "message": "index unavailable",
    }


async def test_unhandled_exception_is_not_swallowed_as_an_app_error() -> None:
    """Edge case: a non-AppError exception (a real bug) must NOT be caught
    by our handler. It should fall through to FastAPI's default handling —
    proving `except AppError` isn't accidentally acting like `except
    Exception` and hiding genuine bugs behind a friendly response."""
    app = create_app()

    @app.get("/_bug")
    async def bug() -> None:
        raise ValueError("this is a real bug, not an anticipated error")

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/_bug")

    assert response.status_code == 500
    # Must NOT look like our clean AppError JSON shape.
    assert "application/json" not in response.headers.get("content-type", "")
