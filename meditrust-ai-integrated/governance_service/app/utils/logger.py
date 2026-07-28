"""
governance_service/app/utils/logger.py
----------------------------------------
Structured JSON logger used across the entire governance service.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """Emits each log record as a single JSON line."""

    SERVICE = "governance-service"

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.SERVICE,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Attach structured extras added via logger.info("...", extra={...})
        for key, value in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "id", "levelname", "levelno",
                "lineno", "module", "msecs", "message", "msg", "name",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "thread", "threadName",
            ):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Return a named logger with structured JSON output."""
    from governance_service.app.config import settings  # avoid circular at module load

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    effective_level = level or settings.LOG_LEVEL
    logger.setLevel(getattr(logging, effective_level.upper(), logging.INFO))
    return logger
