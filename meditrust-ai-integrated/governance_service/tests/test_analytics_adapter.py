"""
governance_service/tests/test_analytics_adapter.py
----------------------------------------------------
Tests for the analytics cascade: PostHog → SQLite → JSONL.
PostHog is disabled in test mode (POSTHOG_ENABLED=false).
"""

from __future__ import annotations

import os
import json
import pytest

from governance_service.app.analytics.adapter import AnalyticsAdapter
from governance_service.app.analytics.sqlite_store import SQLiteStore
from governance_service.app.analytics.jsonl_store import JSONLStore


@pytest.fixture
def isolated_adapter(tmp_path):
    """An adapter with isolated temp storage."""
    db = str(tmp_path / "test.db")
    jsonl = str(tmp_path / "events.jsonl")
    os.environ["SQLITE_PATH"] = db
    os.environ["JSONL_FALLBACK_PATH"] = jsonl
    os.environ["POSTHOG_ENABLED"] = "false"
    return AnalyticsAdapter()


class TestAnalyticsCascade:
    def test_capture_stores_to_sqlite(self, isolated_adapter):
        success, backend = isolated_adapter.capture(
            event_type="meditrust_workflow_started",
            properties={"request_id": "REQ-001", "user_role": "nurse"},
            request_id="REQ-001",
        )
        assert success is True
        assert backend == "sqlite"

    def test_multiple_events_stored(self, isolated_adapter):
        for i in range(5):
            success, backend = isolated_adapter.capture(
                event_type="meditrust_llm_invoked",
                properties={"request_id": f"REQ-{i:03d}", "model": "gemini-1.5-flash"},
                request_id=f"REQ-{i:03d}",
            )
            assert success is True

    def test_audit_write(self, isolated_adapter):
        success = isolated_adapter.write_audit(
            audit_id="AUD-001",
            request_id="REQ-AUDIT-001",
            query_hash="abc123hash",
            input_decision="allow",
            risk_level="low",
            user_role="nurse",
        )
        assert success is True

        record = isolated_adapter.get_audit_record("REQ-AUDIT-001")
        assert record is not None
        assert record["risk_level"] == "low"
        assert record["input_decision"] == "allow"
        # Raw query MUST NOT be in audit
        assert "abc123hash" == record["query_hash"]

    def test_feedback_write(self, isolated_adapter):
        success = isolated_adapter.write_feedback(
            feedback_id="EVT-FEEDBACK-001",
            request_id="REQ-FB-001",
            original_request_id="REQ-ORIG-001",
            rating=4,
            helpful=True,
            user_role="nurse",
        )
        assert success is True

    def test_metrics_summary_returns_data(self, isolated_adapter):
        # Insert some events
        isolated_adapter.capture(
            event_type="meditrust_input_guard_result",
            properties={"decision": "allow", "risk_level": "low", "injection_detected": False, "guard_latency_ms": 12},
            request_id="REQ-METRIC-001",
        )
        isolated_adapter.write_audit(
            audit_id="AUD-METRIC-001",
            request_id="REQ-METRIC-001",
            query_hash="hash001",
            input_decision="allow",
            risk_level="low",
        )

        summary = isolated_adapter.get_metrics_summary(window_hours=24)
        assert "guardrail_stats" in summary
        assert "token_stats" in summary
        assert summary["analytics_backend"] == "sqlite"

    def test_backend_status_returns_dict(self, isolated_adapter):
        status = isolated_adapter.backend_status()
        assert "posthog" in status
        assert "sqlite" in status
        assert "jsonl" in status


class TestJSONLFallback:
    def test_jsonl_appends_record(self, tmp_path):
        path = str(tmp_path / "fallback.jsonl")
        store = JSONLStore(path=path)
        ok = store.append(
            event_id="EVT-001",
            event_type="meditrust_error_occurred",
            properties={"error_code": "TEST", "component": "test"},
        )
        assert ok is True
        assert os.path.exists(path)
        with open(path) as f:
            line = json.loads(f.readline())
        assert line["event_id"] == "EVT-001"

    def test_jsonl_tail(self, tmp_path):
        path = str(tmp_path / "tail.jsonl")
        store = JSONLStore(path=path)
        for i in range(5):
            store.append(f"EVT-{i:03d}", "meditrust_test", {"i": i})
        tail = store.tail(n=3)
        assert len(tail) == 3

    def test_jsonl_is_available(self, tmp_path):
        store = JSONLStore(path=str(tmp_path / "avail.jsonl"))
        assert store.is_available() is True


class TestSQLiteStore:
    def test_schema_initialises(self, tmp_path):
        store = SQLiteStore(db_path=str(tmp_path / "init.db"))
        assert store.is_available() is True

    def test_duplicate_event_ignored(self, tmp_path):
        store = SQLiteStore(db_path=str(tmp_path / "dup.db"))
        ok1 = store.insert_event("EVT-DUP", "meditrust_test", {"x": 1})
        ok2 = store.insert_event("EVT-DUP", "meditrust_test", {"x": 2})  # duplicate
        assert ok1 is True
        assert ok2 is True  # INSERT OR IGNORE — should not raise

    def test_audit_record_roundtrip(self, tmp_path):
        store = SQLiteStore(db_path=str(tmp_path / "audit.db"))
        store.insert_audit(
            audit_id="AUD-RT-001",
            request_id="REQ-RT-001",
            query_hash="rt_hash",
            input_decision="block",
            risk_level="critical",
            user_role="anonymous",
        )
        record = store.get_audit("REQ-RT-001")
        assert record is not None
        assert record["input_decision"] == "block"
        assert "rt_hash" == record["query_hash"]
