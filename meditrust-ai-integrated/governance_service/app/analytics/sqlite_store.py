"""
governance_service/app/analytics/sqlite_store.py
--------------------------------------------------
SQLite-backed analytics and audit store.

Used as:
  1. Primary fallback when PostHog is unavailable.
  2. Audit log for all requests (always written, regardless of PostHog status).
  3. Source of truth for the /metrics/summary endpoint.

Schema:
  - events       : KPI events from all modules
  - audit_log    : Per-request audit trail (query hash, never raw text)
  - feedback     : User feedback submissions
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional

from governance_service.app.config import settings
from governance_service.app.utils.logger import get_logger

log = get_logger(__name__)

_lock = threading.Lock()


class SQLiteStore:
    """Thread-safe SQLite store for analytics events and audit records."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or settings.SQLITE_PATH
        self._ensure_dir()
        self._init_schema()

    def _ensure_dir(self) -> None:
        import os
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

    @contextmanager
    def _get_conn(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(
            self.db_path,
            timeout=settings.SQLITE_TIMEOUT_SECONDS,
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with _lock, self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id    TEXT NOT NULL UNIQUE,
                    event_type  TEXT NOT NULL,
                    request_id  TEXT,
                    session_id  TEXT,
                    user_role   TEXT,
                    properties  TEXT NOT NULL,
                    created_at  TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_events_type      ON events(event_type);
                CREATE INDEX IF NOT EXISTS idx_events_request   ON events(request_id);
                CREATE INDEX IF NOT EXISTS idx_events_created   ON events(created_at);

                CREATE TABLE IF NOT EXISTS audit_log (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_id        TEXT NOT NULL UNIQUE,
                    request_id      TEXT NOT NULL,
                    session_id      TEXT,
                    user_role       TEXT NOT NULL DEFAULT 'anonymous',
                    risk_level      TEXT NOT NULL DEFAULT 'low',
                    input_decision  TEXT NOT NULL,
                    output_decision TEXT,
                    query_hash      TEXT NOT NULL,
                    workflow_stages TEXT,
                    flags           TEXT,
                    created_at      TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_audit_request ON audit_log(request_id);
                CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at);

                CREATE TABLE IF NOT EXISTS feedback (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback_id         TEXT NOT NULL UNIQUE,
                    request_id          TEXT NOT NULL,
                    original_request_id TEXT NOT NULL,
                    rating              INTEGER NOT NULL,
                    helpful             INTEGER NOT NULL,
                    comment_hash        TEXT,
                    user_role           TEXT,
                    created_at          TEXT NOT NULL
                );
            """)
        log.info("SQLite schema initialised.", extra={"db": self.db_path})

    # ── Events ────────────────────────────────────────────────────────────────

    def insert_event(
        self,
        event_id: str,
        event_type: str,
        properties: Dict[str, Any],
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_role: Optional[str] = None,
    ) -> bool:
        try:
            with _lock, self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO events
                        (event_id, event_type, request_id, session_id, user_role, properties, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        event_type,
                        request_id,
                        session_id,
                        user_role,
                        json.dumps(properties, default=str),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
            return True
        except Exception as exc:
            log.error("SQLite event insert failed.", extra={"error": str(exc), "event_type": event_type})
            return False

    # ── Audit log ──────────────────────────────────────────────────────────────

    def insert_audit(
        self,
        audit_id: str,
        request_id: str,
        query_hash: str,
        input_decision: str,
        risk_level: str,
        session_id: Optional[str] = None,
        user_role: str = "anonymous",
        output_decision: Optional[str] = None,
        workflow_stages: Optional[List[str]] = None,
        flags: Optional[List[str]] = None,
    ) -> bool:
        try:
            with _lock, self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO audit_log
                        (audit_id, request_id, session_id, user_role, risk_level,
                         input_decision, output_decision, query_hash, workflow_stages, flags, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        request_id,
                        session_id,
                        user_role,
                        risk_level,
                        input_decision,
                        output_decision,
                        query_hash,
                        json.dumps(workflow_stages or []),
                        json.dumps(flags or []),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
            return True
        except Exception as exc:
            log.error("SQLite audit insert failed.", extra={"error": str(exc)})
            return False

    def get_audit(self, request_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self._get_conn() as conn:
                row = conn.execute(
                    "SELECT * FROM audit_log WHERE request_id = ? LIMIT 1",
                    (request_id,),
                ).fetchone()
                return dict(row) if row else None
        except Exception as exc:
            log.error("SQLite audit fetch failed.", extra={"error": str(exc)})
            return None

    # ── Feedback ───────────────────────────────────────────────────────────────

    def insert_feedback(
        self,
        feedback_id: str,
        request_id: str,
        original_request_id: str,
        rating: int,
        helpful: bool,
        user_role: str,
        comment_hash: Optional[str] = None,
    ) -> bool:
        try:
            with _lock, self._get_conn() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO feedback
                        (feedback_id, request_id, original_request_id, rating, helpful,
                         comment_hash, user_role, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        feedback_id,
                        request_id,
                        original_request_id,
                        rating,
                        int(helpful),
                        comment_hash,
                        user_role,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
            return True
        except Exception as exc:
            log.error("SQLite feedback insert failed.", extra={"error": str(exc)})
            return False

    # ── Metrics aggregation ───────────────────────────────────────────────────

    def get_metrics_summary(self, window_hours: int = 24) -> Dict[str, Any]:
        """
        Aggregate KPI metrics for the dashboard (Member 4 consumption).
        """
        cutoff = f"datetime('now', '-{window_hours} hours')"
        try:
            with self._get_conn() as conn:
                # Guardrail stats from audit_log
                audit_rows = conn.execute(
                    f"SELECT input_decision, risk_level, output_decision FROM audit_log "
                    f"WHERE created_at > {cutoff}"
                ).fetchall()

                total_requests = len(audit_rows)
                allowed = sum(1 for r in audit_rows if r["input_decision"] in ("allow", "redact", "warn"))
                blocked = sum(1 for r in audit_rows if r["input_decision"] == "block")
                escalated = sum(1 for r in audit_rows if r["input_decision"] == "escalate")
                redacted = sum(1 for r in audit_rows if r["input_decision"] == "redact")
                high_risk = sum(1 for r in audit_rows if r["risk_level"] in ("high", "critical"))

                # Token stats from events
                token_rows = conn.execute(
                    f"""
                    SELECT json_extract(properties, '$.tokens_before') as tb,
                           json_extract(properties, '$.tokens_after') as ta,
                           json_extract(properties, '$.tokens_saved') as ts
                    FROM events
                    WHERE event_type = 'meditrust_context_optimized'
                      AND created_at > {cutoff}
                    """
                ).fetchall()

                total_before = sum(r["tb"] or 0 for r in token_rows)
                total_after = sum(r["ta"] or 0 for r in token_rows)
                total_saved = sum(r["ts"] or 0 for r in token_rows)
                avg_reduction = (
                    round(total_saved / max(total_before, 1) * 100, 1)
                    if token_rows else None
                )

                # Latency
                latency_rows = conn.execute(
                    f"""
                    SELECT json_extract(properties, '$.total_latency_ms') as lms
                    FROM events
                    WHERE event_type = 'meditrust_answer_delivered'
                      AND created_at > {cutoff}
                    """
                ).fetchall()
                latencies = [r["lms"] for r in latency_rows if r["lms"] is not None]
                avg_latency = round(sum(latencies) / len(latencies)) if latencies else None

                # LLM calls
                llm_count = conn.execute(
                    f"SELECT COUNT(*) FROM events WHERE event_type = 'meditrust_llm_invoked' AND created_at > {cutoff}"
                ).fetchone()[0]

                # Escalations
                escalation_count = conn.execute(
                    f"SELECT COUNT(*) FROM events WHERE event_type = 'meditrust_escalation_triggered' AND created_at > {cutoff}"
                ).fetchone()[0]

                # Citation validity
                citation_rows = conn.execute(
                    f"""
                    SELECT json_extract(properties, '$.citation_validity_pct') as cvp
                    FROM events
                    WHERE event_type = 'meditrust_output_guard_result'
                      AND created_at > {cutoff}
                    """
                ).fetchall()
                cvps = [r["cvp"] for r in citation_rows if r["cvp"] is not None]
                avg_citation_validity = round(sum(cvps) / len(cvps), 1) if cvps else None

                # Injection attempts
                injection_rows = conn.execute(
                    f"""
                    SELECT COUNT(*) FROM events
                    WHERE event_type = 'meditrust_input_guard_result'
                      AND json_extract(properties, '$.injection_detected') = 1
                      AND created_at > {cutoff}
                    """
                ).fetchone()[0]

                return {
                    "window_hours": window_hours,
                    "guardrail_stats": {
                        "total_requests": total_requests,
                        "allowed": allowed,
                        "blocked": blocked,
                        "escalated": escalated,
                        "redacted": redacted,
                        "injection_attempts": injection_rows,
                        "high_risk_queries": high_risk,
                    },
                    "token_stats": {
                        "total_tokens_before": total_before,
                        "total_tokens_after": total_after,
                        "total_tokens_saved": total_saved,
                        "avg_reduction_pct": avg_reduction,
                    },
                    "avg_total_latency_ms": avg_latency,
                    "total_llm_calls": llm_count,
                    "total_escalations": escalation_count,
                    "citation_validity_pct": avg_citation_validity,
                    "analytics_backend": "sqlite",
                }
        except Exception as exc:
            log.error("Metrics summary query failed.", extra={"error": str(exc)})
            return {"error": str(exc), "analytics_backend": "sqlite"}

    def is_available(self) -> bool:
        try:
            with self._get_conn() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception:
            return False
