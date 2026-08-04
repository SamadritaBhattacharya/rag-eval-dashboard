"""Structured JSON logging.

Configures both `structlog` and the stdlib `logging` module so that *every*
log line — ours and third-party (uvicorn, etc.) — is emitted as one JSON
object per line on stdout, with a consistent `level`, `timestamp`, and
`event` key. That consistency is what makes logs machine-parseable by a log
aggregator (CloudWatch, Datadog, ...) in production.

Call `configure_logging()` exactly once, at process startup. After that,
every module gets its logger the idiomatic structlog way:

    logger = structlog.get_logger(__name__)
    logger.info("chunk_ingested", chunk_id=chunk.id, source=chunk.source_url)

Never use `print()` in library code — it bypasses this entirely and can't be
filtered, redirected, or correlated with the rest of a run's logs.
"""

from __future__ import annotations

import logging
import sys

import structlog

from app.core.config import LogLevel, get_settings


def configure_logging(log_level: LogLevel | None = None) -> None:
    """Wire structlog's processors into stdlib logging's root handler.

    Args:
        log_level: Overrides `Settings.log_level` for this call. Production
            code should call `configure_logging()` with no arguments so the
            level comes from `LOG_LEVEL`; tests pass it explicitly to avoid
            depending on ambient environment/config state.
    """
    resolved_level = log_level or get_settings().log_level

    # Processors that run on EVERY log record, whether it originated from a
    # structlog call or a plain stdlib `logging.getLogger(...)` call (e.g.
    # uvicorn's access logs) — this is what unifies both into one format.
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(resolved_level)
