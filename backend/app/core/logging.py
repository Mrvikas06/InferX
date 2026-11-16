"""Structured Logging Configuration with Correlation Tracking for InferX."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# ContextVar for propagating correlation / request IDs across async tasks
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id_ctx", default=None)


def get_correlation_id() -> Optional[str]:
    """Retrieve current correlation ID from async context."""
    return correlation_id_ctx.get()


def set_correlation_id(correlation_id: str) -> None:
    """Store correlation ID into async context."""
    correlation_id_ctx.set(correlation_id)


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production logging and observability ingestors."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        cid = get_correlation_id()
        if cid:
            log_entry["correlation_id"] = cid

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console formatter with colors and correlation ID display."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        level_color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        cid = get_correlation_id()
        cid_str = f" [{cid[:8]}]" if cid else ""

        message = record.getMessage()
        formatted = (
            f"{timestamp} | {level_color}{record.levelname:<8}{self.RESET} | "
            f"\033[90m{record.name}\033[0m{cid_str} - {message}"
        )

        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def setup_logging(log_level: str = "INFO", log_format: str = "console") -> None:
    """Configure system-wide logging with the selected format."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(ConsoleFormatter())

    root_logger.addHandler(handler)

    # Align standard uvicorn loggers
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        u_logger = logging.getLogger(logger_name)
        u_logger.handlers = []
        u_logger.propagate = True
