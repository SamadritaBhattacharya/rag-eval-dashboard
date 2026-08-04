"""Tests for `app.core.config`."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


def test_settings_defaults_when_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy path: with no LOG_LEVEL set, Settings falls back to INFO."""
    monkeypatch.delenv("LOG_LEVEL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.log_level == "INFO"


def test_settings_rejects_invalid_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """Edge case: an unrecognized LOG_LEVEL fails fast at construction time
    instead of silently passing through to structlog later."""
    monkeypatch.setenv("LOG_LEVEL", "NOT_A_REAL_LEVEL")

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_get_settings_is_a_cached_singleton() -> None:
    """get_settings() must return the same instance on repeat calls, so
    `.env` is parsed once per process rather than on every call site."""
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second
