from __future__ import annotations

import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_LOGGER_NAME = "ai_ticket_platform"


class MaxLevelFilter(logging.Filter):
    """Allow records up to a configured maximum log level."""

    def __init__(self, max_level: int) -> None:
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno <= self.max_level


class RequestContextFilter(logging.Filter):
    """Ensure structured context fields exist on every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        for field in (
            "request_id",
            "tenant_id",
            "user_id",
            "ticket_id",
            "document_id",
            "chunk_id",
            "job_id",
            "operation",
            "event",
            "status",
            "duration_ms",
            "provider",
            "model",
            "attempt",
        ):
            if not hasattr(record, field):
                setattr(record, field, None)

        return True


class JsonFormatter(logging.Formatter):
    """Format log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        structured_fields = (
            "event",
            "operation",
            "status",
            "request_id",
            "tenant_id",
            "user_id",
            "ticket_id",
            "document_id",
            "chunk_id",
            "job_id",
            "duration_ms",
            "provider",
            "model",
            "attempt",
            "status_code",
            "method",
            "path",
            "filename",
            "file_size_bytes",
            "chunk_count",
            "score",
            "top_k",
            "department",
            "priority",
            "confidence",
            "exception_type",
        )

        for field in structured_fields:
            value = getattr(record, field, None)

            if value is not None:
                payload[field] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def parse_log_level(level: str | int) -> int:
    """Convert log level string or integer into logging level."""
    if isinstance(level, int):
        return level

    normalized = level.strip().upper()

    if normalized not in logging._nameToLevel:
        raise ValueError(f"Unsupported log level: {level}")

    return logging._nameToLevel[normalized]


def setup_logging(
    *,
    logger_name: str = DEFAULT_LOGGER_NAME,
    log_dir: str | Path | None = "var/log",
    level: str | int = logging.INFO,
    stdout: bool = True,
    file_logging: bool = True,
) -> logging.Logger:
    """Configure JSON logging for stdout and rotating log files."""
    log_level = parse_log_level(level)

    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    logger.handlers.clear()
    logger.propagate = False

    formatter = JsonFormatter()
    context_filter = RequestContextFilter()

    if stdout:
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setLevel(log_level)
        stdout_handler.setFormatter(formatter)
        stdout_handler.addFilter(context_filter)
        logger.addHandler(stdout_handler)

    if file_logging:
        if log_dir is None:
            raise ValueError("log_dir must be provided when file_logging=True")

        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        date_suffix = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        info_log_path = log_path / f"ai-ticket-platform-info-{date_suffix}.log"
        error_log_path = log_path / f"ai-ticket-platform-error-{date_suffix}.log"

        info_handler = logging.handlers.RotatingFileHandler(
            info_log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        info_handler.setLevel(logging.DEBUG)
        info_handler.addFilter(MaxLevelFilter(logging.WARNING))
        info_handler.addFilter(context_filter)
        info_handler.setFormatter(formatter)
        logger.addHandler(info_handler)

        error_handler = logging.handlers.RotatingFileHandler(
            error_log_path,
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.addFilter(context_filter)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)

    logger.info(
        "Logging initialized",
        extra={
            "event": "logging_initialized",
            "operation": "setup_logging",
            "status": "success",
        },
    )

    return logger


def get_logger(name: str) -> logging.Logger:
    """Return module-specific application logger."""
    if name.startswith(DEFAULT_LOGGER_NAME):
        return logging.getLogger(name)

    return logging.getLogger(f"{DEFAULT_LOGGER_NAME}.{name}")


def bind_logger(
    logger: logging.Logger,
    *,
    request_id: str | None = None,
    tenant_id: str | None = None,
    user_id: str | None = None,
    ticket_id: str | None = None,
    document_id: str | None = None,
    job_id: str | None = None,
) -> logging.LoggerAdapter:
    """Attach structured context to logger."""
    return logging.LoggerAdapter(
        logger,
        {
            "request_id": request_id,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "ticket_id": ticket_id,
            "document_id": document_id,
            "job_id": job_id,
        },
    )


def log_step(
    logger: logging.Logger | logging.LoggerAdapter,
    *,
    event: str,
    operation: str,
    status: str,
    message: str,
    **extra: Any,
) -> None:
    """Log successful or in-progress operation."""
    logger.info(
        message,
        extra={
            "event": event,
            "operation": operation,
            "status": status,
            **extra,
        },
    )


def log_warning(
    logger: logging.Logger | logging.LoggerAdapter,
    *,
    event: str,
    operation: str,
    message: str,
    **extra: Any,
) -> None:
    """Log warning with structured metadata."""
    logger.warning(
        message,
        extra={
            "event": event,
            "operation": operation,
            "status": "warning",
            **extra,
        },
    )


def log_failure(
    logger: logging.Logger | logging.LoggerAdapter,
    *,
    event: str,
    operation: str,
    message: str,
    exc: Exception,
    **extra: Any,
) -> None:
    """Log failed operation with exception details."""
    logger.error(
        message,
        extra={
            "event": event,
            "operation": operation,
            "status": "failed",
            "exception_type": type(exc).__name__,
            **extra,
        },
        exc_info=True,
    )
