"""
governance_service/app/analytics/adapter.py
---------------------------------------------
Analytics cascade adapter: PostHog → SQLite → JSONL

Every event capture attempt:
  1. Tries PostHog.
  2. On failure, falls back to SQLite.
  3. On SQLite failure, appends to JSONL.
  4. Emits a structured log regardless of which backend received it.

The adapter is a singleton — one instance shared across all request handlers.
Thread-safe: all three backends use their own locking.

INTEGRATION NOTE
----------------
Any module can call the governance service analytics endpoint:
  POST http://127.0.0.1:8002/api/v1/analytics/capture
Or, if running in the same process, import and call directly:
  from governance_service.app.analytics.adapter import analytics_adapter
  analytics_adapter.capture(event_type, properties, ...)
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from governance_service.app.analytics.events import EventType
from governance_service.app.analytics.jsonl_store import JSONLStore
from governance_service.app.analytics.posthog_client import PostHogClient
from governance_service.app.analytics.sqlite_store import SQLiteStore
from governance_service.app.utils.id_generator import new_event_id
from governance_service.app.utils.logger import get_logger

log = get_logger(__name__)


class AnalyticsAdapter:
    """
    Cascade analytics adapter.
    Audit writes (SQLite audit_log) happen INDEPENDENTLY of the event cascade —
    the audit log is always written when requested.
    """

    def __init__(self) -> None:
        self._posthog = PostHogClient()
        self._sqlite = SQLiteStore()
        self._jsonl = JSONLStore()
        log.info("AnalyticsAdapter initialised.")

    # ── Public: capture event ─────────────────────────────────────────────────

    def capture(
        self,
        event_type: str,
        properties: Dict[str, Any],
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_role: Optional[str] = None,
        distinct_id: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Store a KPI event through the cascade.

        Returns (success: bool, backend_used: str).
        """
        event_id = new_event_id()
        ph_distinct = distinct_id or session_id or "anonymous"

        # ── ALWAYS write to SQLite events table (audit + KPI source) ──────────
        sqlite_ok = self._sqlite.insert_event(
            event_id=event_id,
            event_type=event_type,
            properties=properties,
            request_id=request_id,
            session_id=session_id,
            user_role=user_role,
        )

        # ── Try PostHog ──────────────────────────────────────────────────────
        if self._posthog.is_available:
            ph_ok = self._posthog.capture(
                distinct_id=ph_distinct,
                event=event_type,
                properties={**properties, "request_id": request_id, "user_role": user_role},
            )
            if ph_ok:
                log.debug("Event stored: posthog+sqlite", extra={"event_id": event_id})
                return True, "posthog"
            else:
                log.info("PostHog unavailable; SQLite captured.", extra={"event_id": event_id})

        if sqlite_ok:
            return True, "sqlite"

        # ── Last resort: JSONL ────────────────────────────────────────────────
        jsonl_ok = self._jsonl.append(
            event_id=event_id,
            event_type=event_type,
            properties=properties,
            request_id=request_id,
            session_id=session_id,
            user_role=user_role,
        )

        if jsonl_ok:
            log.warning("SQLite failed; event stored in JSONL.", extra={"event_id": event_id})
            return True, "jsonl"

        log.error("ALL analytics backends failed!", extra={"event_id": event_id, "event_type": event_type})
        return False, "none"

    # ── Public: audit write ───────────────────────────────────────────────────

    def write_audit(
        self,
        audit_id: str,
        request_id: str,
        query_hash: str,
        input_decision: str,
        risk_level: str,
        session_id: Optional[str] = None,
        user_role: str = "anonymous",
        output_decision: Optional[str] = None,
        workflow_stages: Optional[list] = None,
        flags: Optional[list] = None,
    ) -> bool:
        return self._sqlite.insert_audit(
            audit_id=audit_id,
            request_id=request_id,
            session_id=session_id,
            user_role=user_role,
            risk_level=risk_level,
            input_decision=input_decision,
            output_decision=output_decision,
            query_hash=query_hash,
            workflow_stages=workflow_stages,
            flags=flags,
        )

    # ── Public: feedback write ────────────────────────────────────────────────

    def write_feedback(
        self,
        feedback_id: str,
        request_id: str,
        original_request_id: str,
        rating: int,
        helpful: bool,
        user_role: str,
        comment_hash: Optional[str] = None,
    ) -> bool:
        return self._sqlite.insert_feedback(
            feedback_id=feedback_id,
            request_id=request_id,
            original_request_id=original_request_id,
            rating=rating,
            helpful=helpful,
            user_role=user_role,
            comment_hash=comment_hash,
        )

    # ── Public: get metrics ───────────────────────────────────────────────────

    def get_metrics_summary(self, window_hours: int = 24) -> Dict[str, Any]:
        return self._sqlite.get_metrics_summary(window_hours=window_hours)

    def get_audit_record(self, request_id: str) -> Optional[Dict[str, Any]]:
        return self._sqlite.get_audit(request_id=request_id)

    # ── Public: health status ─────────────────────────────────────────────────

    def backend_status(self) -> Dict[str, Any]:
        return {
            "posthog": self._posthog.status(),
            "sqlite": {"available": self._sqlite.is_available(), "path": self._sqlite.db_path},
            "jsonl": {"available": self._jsonl.is_available(), "path": self._jsonl.path},
        }


# ---------------------------------------------------------------------------
# Module-level singleton (imported by API routes)
# ---------------------------------------------------------------------------

analytics_adapter = AnalyticsAdapter()
