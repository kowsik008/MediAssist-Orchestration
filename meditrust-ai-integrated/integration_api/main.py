from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from integration_api.config import Settings, get_settings
from integration_api.models import EvidenceRequest, FeedbackRequest, WorkflowRequest


app = FastAPI(title="MediTrust AI Integration Gateway", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def _request(
    method: str,
    url: str,
    settings: Settings,
    *,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        with httpx.Client(timeout=settings.request_timeout_seconds) as client:
            response = client.request(method, url, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        try:
            detail: Any = exc.response.json()
        except Exception:  # noqa: BLE001
            detail = exc.response.text
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "DEPENDENCY_UNAVAILABLE",
                "message": f"Required backend dependency is unavailable: {url}",
            },
        ) from exc


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "integration_api",
        "status": "running",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.post("/api/v1/workflows/invoke")
def invoke_workflow(request: WorkflowRequest) -> dict[str, Any]:
    settings = get_settings()
    endpoint = (
        "/api/v1/invoke/baseline"
        if request.mode == "baseline"
        else "/api/v1/invoke/optimized"
    )
    payload = {
        "query": request.query,
        "user_role": request.user_role,
        "request_id": request.request_id,
        "session_id": request.session_id,
        "top_k": request.top_k,
        "status_filter": request.status_filter,
        "source_type": request.source_type,
        "document_ids": request.document_ids,
        "tags": request.tags,
        "metadata": request.metadata,
    }
    result = _request(
        "POST",
        f"{settings.orchestration_service_url}{endpoint}",
        settings,
        payload=payload,
    )
    final_status = str(result.get("final_status", "completed"))
    requires_human_review = final_status in {
        "escalated",
        "escalated_by_input_guard",
        "blocked_by_input_guard",
        "blocked_by_output_guard",
        "insufficient_evidence",
    }
    validation_status = {
        "blocked_by_input_guard": "block",
        "blocked_by_output_guard": "block",
        "escalated_by_input_guard": "escalate",
        "escalated": "escalate",
        "insufficient_evidence": "escalate",
        "completed_after_regeneration": "pass_with_warning",
    }.get(final_status, "pass")
    raw_metrics = result.get("metrics", {})
    result.update(
        {
            "schema_version": "1.0",
            "cautions": [
                *result.get("warnings", []),
                *result.get("negative_statements", []),
            ],
            "risk_level": result.get("classification", {}).get("risk", "medium"),
            "validation_status": validation_status,
            "requires_human_review": requires_human_review,
            "workflow_trace": result.get("trace", []),
            "metrics": {
                **raw_metrics,
                "tokens_before_optimization": raw_metrics.get("token_count_before", 0),
                "tokens_after_optimization": raw_metrics.get("token_count_after", 0),
                "tokens_saved": max(
                    0,
                    raw_metrics.get("token_count_before", 0)
                    - raw_metrics.get("token_count_after", 0),
                ),
                "total_latency_ms": raw_metrics.get("latency_ms", 0),
            },
        }
    )
    return result


@app.post("/api/v1/evidence")
def retrieve_evidence(request: EvidenceRequest) -> dict[str, Any]:
    settings = get_settings()
    return _request(
        "POST",
        f"{settings.knowledge_service_url}/retrieve",
        settings,
        payload=request.model_dump(exclude_none=True),
    )


@app.get("/api/v1/sources")
def sources() -> Any:
    settings = get_settings()
    return _request("GET", f"{settings.knowledge_service_url}/sources", settings)


@app.get("/api/v1/audit/recent")
def recent_audit(
    window_hours: int = Query(default=24, ge=1, le=8760),
    limit: int = Query(default=100, ge=1, le=1000),
) -> Any:
    settings = get_settings()
    return _request(
        "GET",
        (
            f"{settings.governance_service_url}/api/v1/audit/recent"
            f"?window_hours={window_hours}&limit={limit}"
        ),
        settings,
    )


@app.post("/api/v1/feedback")
def submit_feedback(request: FeedbackRequest) -> dict[str, Any]:
    settings = get_settings()
    payload = {
        "request_id": request.request_id,
        "original_request_id": request.request_id,
        "rating": request.rating,
        "helpful": request.helpful,
        "comment": request.comment,
        "user_role": "anonymous" if request.user_role == "public" else request.user_role,
    }
    return _request(
        "POST",
        f"{settings.governance_service_url}/api/v1/feedback",
        settings,
        payload=payload,
    )


@app.get("/api/v1/metrics")
def metrics(window_hours: int = Query(default=24, ge=1, le=720)) -> dict[str, Any]:
    settings = get_settings()
    return _request(
        "GET",
        f"{settings.governance_service_url}/api/v1/metrics/summary?window_hours={window_hours}",
        settings,
    )


@app.get("/api/v1/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    definitions = [
        ("knowledge_service", f"{settings.knowledge_service_url}/health"),
        ("governance_service", f"{settings.governance_service_url}/api/v1/health"),
        ("orchestration_service", f"{settings.orchestration_service_url}/health"),
    ]
    dependencies: list[dict[str, Any]] = []
    with httpx.Client(timeout=3.0) as client:
        for name, url in definitions:
            started = time.perf_counter()
            try:
                response = client.get(url)
                payload = response.json()
                reported = str(payload.get("status", "ok")).lower()
                if not response.is_success or reported in {"unhealthy", "unavailable", "error"}:
                    status = "unavailable"
                elif reported in {"degraded", "warning"}:
                    status = "degraded"
                else:
                    status = "ok"
                detail = reported
            except Exception as exc:  # noqa: BLE001
                status = "unavailable"
                detail = exc.__class__.__name__
            dependencies.append(
                {
                    "name": name,
                    "status": status,
                    "mode": "integrated" if status == "ok" else "fallback",
                    "latency_ms": int((time.perf_counter() - started) * 1000),
                    "detail": detail,
                }
            )
    overall = (
        "degraded"
        if any(item["status"] == "unavailable" for item in dependencies)
        else "healthy"
    )
    return {
        "schema_version": "1.0",
        "service": "integration_api",
        "status": overall,
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": settings.app_mode,
        "dependencies": dependencies,
    }
