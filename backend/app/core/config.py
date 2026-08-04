"""Application configuration.

All runtime configuration is read from environment variables (via a `.env`
file locally, real env vars in deployment) through a single Pydantic
`Settings` class. Nothing in this codebase should call `os.getenv` directly —
route every new config value through here so it is validated once, at
startup, in one place.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Typed, validated application configuration.

    Values are loaded from environment variables (case-insensitive) with a
    `.env` file in `backend/` as a local-development fallback. Required
    values with no default will raise `pydantic.ValidationError` on
    instantiation, which is what gives us fail-fast startup: a missing var
    crashes immediately with a clear message instead of surfacing as a
    mysterious `None` deep in the pipeline later.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignore unrelated env vars (PATH, etc.) instead of erroring on them.
        extra="ignore",
    )

    # ---- Phase 0 ----
    log_level: LogLevel = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide `Settings` singleton.

    Cached with `lru_cache` so `.env` / the environment is parsed once per
    process, not on every call site that needs config. Tests bypass the
    cache by calling `Settings(...)` directly or clearing
    `get_settings.cache_clear()`.
    """
    return Settings()
