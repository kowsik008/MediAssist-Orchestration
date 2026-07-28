from fastapi.testclient import TestClient

from integration_api import main


client = TestClient(main.app)


def test_root_contract() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "integration_api"


def test_workflow_contract_normalizes_response(monkeypatch) -> None:
    def fake_request(*args, **kwargs):
        return {
            "request_id": "REQ-TEST",
            "answer": "Grounded answer",
            "warnings": ["Not patient-specific guidance"],
            "negative_statements": [],
            "classification": {"risk": "low"},
            "trace": [{"node": "finish", "event_type": "completed"}],
            "metrics": {
                "latency_ms": 100,
                "token_count_before": 1000,
                "token_count_after": 600,
            },
            "final_status": "completed",
            "cache_hit": False,
            "citations": [],
        }

    monkeypatch.setattr(main, "_request", fake_request)
    response = client.post(
        "/api/v1/workflows/invoke",
        json={
            "request_id": "REQ-TEST",
            "query": "What is approved hand hygiene guidance?",
            "user_role": "nurse",
            "mode": "optimized",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "1.0"
    assert payload["validation_status"] == "pass"
    assert payload["requires_human_review"] is False
    assert payload["metrics"]["tokens_saved"] == 400
    assert payload["workflow_trace"]


def test_invalid_workflow_role_is_rejected() -> None:
    response = client.post(
        "/api/v1/workflows/invoke",
        json={"query": "test query", "user_role": "superuser"},
    )
    assert response.status_code == 422
