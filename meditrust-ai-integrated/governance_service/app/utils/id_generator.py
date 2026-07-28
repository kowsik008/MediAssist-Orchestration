"""
governance_service/app/utils/id_generator.py
----------------------------------------------
Deterministic ID and hash helpers.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone


def new_request_id() -> str:
    return f"REQ-{uuid.uuid4().hex[:12].upper()}"


def new_audit_id() -> str:
    return f"AUD-{uuid.uuid4().hex[:16].upper()}"


def new_event_id() -> str:
    return f"EVT-{uuid.uuid4().hex[:12].upper()}"


def hash_query(query: str) -> str:
    """SHA-256 of the raw query — stored in audit, never the raw text."""
    return hashlib.sha256(query.encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
