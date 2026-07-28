"""
governance_service/app/analytics/jsonl_store.py
-------------------------------------------------
JSONL last-resort fallback. Appends one JSON object per line to a file.
Used only when BOTH PostHog and SQLite have failed.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from governance_service.app.config import settings
from governance_service.app.utils.logger import get_logger

log = get_logger(__name__)

_lock = threading.Lock()


class JSONLStore:
    """Append-only JSONL event store — the last line of defence."""

    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path or settings.JSONL_FALLBACK_PATH
        self._ensure_dir()

    def _ensure_dir(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)

    def append(
        self,
        event_id: str,
        event_type: str,
        properties: Dict[str, Any],
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_role: Optional[str] = None,
    ) -> bool:
        record = {
            "event_id": event_id,
            "event_type": event_type,
            "request_id": request_id,
            "session_id": session_id,
            "user_role": user_role,
            "properties": properties,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            with _lock:
                with open(self.path, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps(record, default=str) + "\n")
            log.debug("JSONL event appended.", extra={"event_type": event_type, "path": self.path})
            return True
        except Exception as exc:
            log.error("JSONL append failed.", extra={"error": str(exc), "path": self.path})
            return False

    def is_available(self) -> bool:
        try:
            dir_path = os.path.dirname(os.path.abspath(self.path))
            return os.access(dir_path, os.W_OK)
        except Exception:
            return False

    def tail(self, n: int = 50) -> list:
        """Return the last `n` records — used by health endpoint."""
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                lines = fh.readlines()
            return [json.loads(line) for line in lines[-n:] if line.strip()]
        except FileNotFoundError:
            return []
        except Exception as exc:
            log.error("JSONL tail failed.", extra={"error": str(exc)})
            return []
