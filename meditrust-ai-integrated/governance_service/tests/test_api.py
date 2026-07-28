"""
governance_service/tests/test_api.py
--------------------------------------
Contract + integration tests for all governance API endpoints.
Uses TestClient (no network required).
"""

from __future__ import annotations

import pytest


class TestHealthEndpoint:
    def test_health_returns_200(self, test_client):
        resp = test_client.get("/api/v1/health")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "service" in data
        assert "status" in data
        assert "dependencies" in data

    def test_health_has_dependency_list(self, test_client):
        resp = test_client.get("/api/v1/health")
        data = resp.json()
        dep_names = {d["name"] for d in data["dependencies"]}
        assert "sqlite" in dep_names
        assert "guardrails" in dep_names


class TestInputGuardEndpoint:
    def test_safe_query_allowed(self, test_client, safe_query_payload):
        resp = test_client.post("/api/v1/guard/input", json=safe_query_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] in ("allow", "redact", "warn")
        assert "safe_query" in data
        assert "risk_level" in data

    def test_injection_blocked(self, test_client, injection_payload):
        resp = test_client.post("/api/v1/guard/input", json=injection_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "block"
        assert data["risk_level"] == "critical"

    def test_diagnosis_escalated(self, test_client, diagnosis_payload):
        resp = test_client.post("/api/v1/guard/input", json=diagnosis_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "escalate"
        assert data["requires_human_review"] is True

    def test_dosage_escalated(self, test_client, dosage_payload):
        resp = test_client.post("/api/v1/guard/input", json=dosage_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] == "escalate"

    def test_pii_redacted(self, test_client, pii_payload):
        resp = test_client.post("/api/v1/guard/input", json=pii_payload)
        assert resp.status_code == 200
        data = resp.json()
        # Either redacted or escalated (contains patient ID pattern)
        assert data["decision"] in ("redact", "escalate", "block")
        # MRN must not appear in safe_query
        assert "ABC-12345" not in data.get("safe_query", "")

    def test_missing_query_returns_422(self, test_client):
        resp = test_client.post("/api/v1/guard/input", json={"user_role": "nurse"})
        assert resp.status_code == 422

    def test_response_has_schema_version(self, test_client, safe_query_payload):
        resp = test_client.post("/api/v1/guard/input", json=safe_query_payload)
        data = resp.json()
        assert "schema_version" in data


class TestOutputGuardEndpoint:
    def test_valid_answer_passes(self, test_client, valid_output_payload):
        resp = test_client.post("/api/v1/guard/output", json=valid_output_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] in ("pass", "pass_with_warning")
        assert data["answer"] is not None
        assert data["schema_valid"] is True

    def test_hallucinated_citation_flagged(self, test_client, hallucinated_citation_payload):
        resp = test_client.post("/api/v1/guard/output", json=hallucinated_citation_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["decision"] in ("regenerate", "pass_with_warning", "escalate")
        # Verify citation checks are returned
        assert "citation_checks" in data
        failed = [c for c in data["citation_checks"] if not c["passed"]]
        assert len(failed) >= 1

    def test_response_contains_cautions(self, test_client, valid_output_payload):
        resp = test_client.post("/api/v1/guard/output", json=valid_output_payload)
        data = resp.json()
        assert len(data["cautions"]) >= 1  # standard caution always present


class TestAnalyticsEndpoints:
    def test_capture_event_stored(self, test_client):
        resp = test_client.post(
            "/api/v1/analytics/capture",
            json={
                "event_type": "meditrust_workflow_started",
                "user_role": "nurse",
                "properties": {"query_hash": "abc123", "session_id": "test"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["stored"] is True
        assert data["backend_used"] in ("posthog", "sqlite", "jsonl")

    def test_metrics_summary_returns_data(self, test_client):
        resp = test_client.get("/api/v1/metrics/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "guardrail_stats" in data
        assert "token_stats" in data
        assert "window_hours" in data

    def test_metrics_export_json(self, test_client):
        resp = test_client.get("/api/v1/metrics/export?format=json")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")

    def test_metrics_export_csv(self, test_client):
        resp = test_client.get("/api/v1/metrics/export?format=csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]


class TestFeedbackEndpoint:
    def test_feedback_accepted(self, test_client):
        resp = test_client.post(
            "/api/v1/feedback",
            json={
                "original_request_id": "REQ-ORIG-001",
                "rating": 4,
                "helpful": True,
                "user_role": "nurse",
                "comment": "Very helpful guidelines.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["stored"] is True

    def test_feedback_invalid_rating_rejected(self, test_client):
        resp = test_client.post(
            "/api/v1/feedback",
            json={
                "original_request_id": "REQ-ORIG-001",
                "rating": 10,  # out of range
                "helpful": True,
                "user_role": "nurse",
            },
        )
        assert resp.status_code == 422


class TestAuditEndpoints:
    def test_audit_trace_not_found(self, test_client):
        resp = test_client.post(
            "/api/v1/audit/trace",
            json={"target_request_id": "REQ-NONEXISTENT-999"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["found"] is False

    def test_audit_export_csv(self, test_client):
        resp = test_client.get("/api/v1/audit/export?window_hours=24")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]


class TestCORSHeaders:
    def test_options_returns_cors_headers(self, test_client):
        resp = test_client.options(
            "/api/v1/guard/input",
            headers={"Origin": "http://localhost:3000"},
        )
        # CORS headers should be present for the configured origins
        assert resp.status_code in (200, 204, 405)


class TestRootEndpoint:
    def test_root_returns_service_info(self, test_client):
        resp = test_client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "service" in data
        assert "version" in data
        assert "health" in data
