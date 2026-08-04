"""Tests for `app.core.logging`.

These assert on the *structure* of emitted logs (required keys, level
filtering) rather than exact message text — logs are a machine-readable
contract, and that's what we verify.
"""

from __future__ import annotations

import json

import pytest
import structlog

from app.core.logging import configure_logging


def test_configure_logging_emits_json_with_required_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Happy path: a log call produces one JSON line with event/level/timestamp."""
    configure_logging(log_level="INFO")
    logger = structlog.get_logger("test")

    logger.info("something_happened", user_id=42)

    line = capsys.readouterr().out.strip().splitlines()[-1]
    payload = json.loads(line)

    assert payload["event"] == "something_happened"
    assert payload["level"] == "info"
    assert "timestamp" in payload
    assert payload["user_id"] == 42


def test_configure_logging_filters_below_configured_level(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Edge case: with level=WARNING, an INFO call must be dropped entirely."""
    configure_logging(log_level="WARNING")
    logger = structlog.get_logger("test")

    logger.info("should_be_filtered_out")
    logger.warning("should_appear")

    lines = [line for line in capsys.readouterr().out.strip().splitlines() if line]

    assert len(lines) == 1
    assert json.loads(lines[0])["event"] == "should_appear"
