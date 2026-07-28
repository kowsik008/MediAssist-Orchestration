"""
governance_service/app/api/routes/analytics.py
------------------------------------------------
POST /api/v1/analytics/capture  — Capture a KPI event (any module)
GET  /api/v1/metrics/summary    — Aggregated KPI dashboard data (Member 4)
GET  /api/v1/metrics/export     — Export metrics as JSON or CSV
"""

from __future__ import annotations

import csv
import io
import json
from typing import Optional

from fastapi import APIRouter, Body, Query
from fastapi.responses import JSONResponse, StreamingResponse

from governance_service.app.analytics.adapter import analytics_adapter
from governance_service.app.analytics.events import EventType
from governance_service.app.config import settings
from governance_service.app.utils.id_generator import new_event_id, new_request_id
from governance_service.app.utils.logger import get_logger

from shared.schemas.governance import (
    AnalyticsCaptureRequest,
    AnalyticsCaptureResponse,
    MetricsSummaryResponse,
    GuardrailStats,
    RetrievalStats,
    TokenStats,
)

log = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# POST /analytics/capture
# ---------------------------------------------------------------------------

@router.post(
    "/analytics/capture",
    response_model=AnalyticsCaptureResponse,
    summary="Capture a KPI event from any module",
    description=(
        "Stores a KPI event through the cascade: PostHog → SQLite → JSONL. "
        "Raw query text must NEVER appear in properties."
    ),
)
async def capture_event(request: AnalyticsCaptureRequest = Body(...)) -> AnalyticsCaptureResponse:
    log.debug(
        "Analytics capture received",
        extra={"event_type": request.event_type, "request_id": request.request_id},
    )

    # Merge token/latency metrics into properties if provided
    props = dict(request.properties)
    if request.token_metrics:
        props.update(request.token_metrics.model_dump())
    if request.latency_metrics:
        props.update(request.latency_metrics.model_dump())

    success, backend = analytics_adapter.capture(
        event_type=request.event_type,
        properties=props,
        request_id=request.request_id,
        session_id=request.session_id,
        user_role=request.user_role,
    )

    event_id = new_event_id()

    return AnalyticsCaptureResponse(
        request_id=request.request_id,
        stored=success,
        backend_used=backend,
        event_id=event_id,
    )


# ---------------------------------------------------------------------------
# GET /metrics/summary
# ---------------------------------------------------------------------------

@router.get(
    "/metrics/summary",
    response_model=MetricsSummaryResponse,
    summary="Aggregated KPI metrics for the governance dashboard",
    description="Returns guardrail, token, latency and citation metrics for the last N hours.",
)
async def metrics_summary(
    window_hours: int = Query(default=24, ge=1, le=720, description="Look-back window in hours"),
) -> MetricsSummaryResponse:
    data = analytics_adapter.get_metrics_summary(window_hours=window_hours)

    gs = data.get("guardrail_stats", {})
    ts = data.get("token_stats", {})

    return MetricsSummaryResponse(
        request_id=new_request_id(),
        window_hours=window_hours,
        guardrail_stats=GuardrailStats(
            total_requests=gs.get("total_requests", 0),
            allowed=gs.get("allowed", 0),
            blocked=gs.get("blocked", 0),
            escalated=gs.get("escalated", 0),
            redacted=gs.get("redacted", 0),
            injection_attempts=gs.get("injection_attempts", 0),
            high_risk_queries=gs.get("high_risk_queries", 0),
        ),
        retrieval_stats=RetrievalStats(),  # populated by Member 1 events
        token_stats=TokenStats(
            total_tokens_before=ts.get("total_tokens_before", 0),
            total_tokens_after=ts.get("total_tokens_after", 0),
            total_tokens_saved=ts.get("total_tokens_saved", 0),
            avg_reduction_pct=ts.get("avg_reduction_pct"),
        ),
        analytics_backend=data.get("analytics_backend", "sqlite"),
        total_llm_calls=data.get("total_llm_calls", 0),
        total_escalations=data.get("total_escalations", 0),
        avg_total_latency_ms=data.get("avg_total_latency_ms"),
        citation_validity_pct=data.get("citation_validity_pct"),
    )


# ---------------------------------------------------------------------------
# GET /metrics/export
# ---------------------------------------------------------------------------

@router.get(
    "/metrics/export",
    summary="Export KPI metrics as JSON or CSV",
    description="Download the metrics summary in machine-readable format.",
)
async def metrics_export(
    format: str = Query(default="json", pattern="^(json|csv)$"),
    window_hours: int = Query(default=24, ge=1, le=720),
) -> StreamingResponse:
    data = analytics_adapter.get_metrics_summary(window_hours=window_hours)

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        # Flatten nested dict to rows
        rows = [["metric", "value"]]
        _flatten(data, rows)
        writer.writerows(rows)

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=meditrust_metrics.csv"},
        )

    return StreamingResponse(
        io.BytesIO(json.dumps(data, indent=2).encode()),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=meditrust_metrics.json"},
    )


def _flatten(d: dict, rows: list, prefix: str = "") -> None:
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            _flatten(v, rows, prefix=key)
        else:
            rows.append([key, v])
