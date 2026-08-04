"""Tests for `app.core.errors`."""

from __future__ import annotations

import pytest

from app.core.errors import (
    AppError,
    ConfigError,
    GenerationError,
    GoldenDatasetError,
    JudgeError,
    RetrievalError,
)


@pytest.mark.parametrize(
    ("exc_cls", "expected_status"),
    [
        (ConfigError, 500),
        (GoldenDatasetError, 500),
        (RetrievalError, 500),
        (GenerationError, 502),
        (JudgeError, 502),
    ],
)
def test_error_subclasses_carry_expected_status_code(
    exc_cls: type[AppError], expected_status: int
) -> None:
    """Each concrete error type maps to the HTTP status the exception
    middleware (Step 5) will translate it to."""
    error = exc_cls("something went wrong")

    assert isinstance(error, AppError)
    assert error.status_code == expected_status
    assert error.message == "something went wrong"


def test_app_error_subclasses_are_catchable_as_app_error() -> None:
    """A caller that only knows about AppError can still catch any
    concrete subclass — this is what lets the middleware have one handler
    for every intentional error type."""
    with pytest.raises(AppError):
        raise RetrievalError("index unavailable")


def test_unrelated_exceptions_are_not_app_errors() -> None:
    """A stdlib exception must NOT be mistaken for one of ours — this is
    what keeps a broad 'except AppError' from silently swallowing real bugs."""
    assert not isinstance(ValueError("oops"), AppError)
