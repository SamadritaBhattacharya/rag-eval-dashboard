"""Application-specific exception hierarchy.

Every intentional, anticipated failure in this codebase raises a subclass of
`AppError` — never a bare `Exception` or a stdlib exception directly. That
convention is what lets a single FastAPI exception-handler (Step 5) translate
known error types to clean HTTP responses via `error.status_code`, while any
*unanticipated* exception (a genuine bug) is left uncaught, bubbles up,
gets logged with a full traceback, and surfaces as a plain 500 — instead of
being silently swallowed by an overly broad `except Exception`.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all application-raised errors.

    Subclasses set `status_code` to the HTTP status the exception middleware
    should respond with. Defaults to 500 (internal failure) unless
    overridden.
    """

    status_code: int = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ConfigError(AppError):
    """Configuration is invalid or missing at a point after startup.

    Startup validation (`Settings`) should catch most config problems
    before the app ever serves traffic; this covers config checked lazily,
    on a specific code path.
    """


class GoldenDatasetError(AppError):
    """The golden dataset failed to load or failed schema validation.

    Our own committed data being malformed is an internal-server problem,
    not an upstream one — status 500.
    """


class RetrievalError(AppError):
    """A retrieval component (semantic, keyword, hybrid, or reranker)
    failed to return results.

    The vector store and BM25 index are local infrastructure we run, not a
    third party — so a failure here is ours to own, status 500.
    """


class GenerationError(AppError):
    """The generation step (Groq LLM call) failed or returned an unusable
    response.

    This wraps a genuinely external dependency (Groq's API), so it's
    reported as 502 Bad Gateway — this server, acting as a gateway, got a
    bad response from an upstream service.
    """

    status_code = 502


class JudgeError(AppError):
    """The Ragas judge failed to score a case.

    Also backed by the external Groq API — same 502 reasoning as
    `GenerationError`.
    """

    status_code = 502
