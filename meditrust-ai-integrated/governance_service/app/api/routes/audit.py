"""
governance_service/app/api/routes/audit.py
--------------------------------------------
POST /api/v1/audit/trace  — Look up audit record for a request ID
GET  /api/v1/audit/export — Export audit CSV (compliance officer)
"""

from __future__ import annotations

import csv
import io
import json

from fastapi import APIRouter, Body, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from governance_service.app.analytics.adapter import analytics_adapter
from governance_service.app.analytics.sqlite_store import SQLiteStore
from governance_service.app.config import settings
from governance_service.app.utils.id_generator import new_request_id
from governance_service.app.utils.logger import get_logger

from shared.schemas.governance import AuditRecord, AuditTraceRequest, AuditTraceResponse

log = get_logger(__name__)
router = APIRouter()


@router.get(
    "/audit/recent",
    summary="Return recent scrubbed audit records as JSON",
)
async def audit_recent(
    window_hours: int = Query(default=24, ge=1, le=8760),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict]:
    store = SQLiteStore()
    cutoff_expr = f"datetime('now', '-{window_hours} hours')"
    try:
        with store._get_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT audit_id, request_id, session_id, user_role, risk_level,
                       input_decision, output_decision, query_hash, workflow_stages,
                       flags, created_at
                FROM audit_log
                WHERE created_at > {cutoff_expr}
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "AUDIT_READ_FAILURE", "message": str(exc)},
        ) from exc
    return [dict(row) for row in rows]


@router.post(
    "/audit/trace",
    response_model=AuditTraceResponse,
    summary="Retrieve audit record for a specific request ID",
    description=(
        "Returns the audit trail for a given request. Raw query text is never "
        "returned — only the query hash and governance decisions."
    ),
)
async def audit_trace(request: AuditTraceRequest = Body(...)) -> AuditTraceResponse:
    record = analytics_adapter.get_audit_record(request.target_request_id)

    if not record:
        return AuditTraceResponse(
            request_id=request.request_id,
            record=None,
            found=False,
        )

    return AuditTraceResponse(
        request_id=request.request_id,
        found=True,
        record=AuditRecord(
            audit_id=record.get("audit_id", ""),
            request_id=record.get("request_id", ""),
            session_id=record.get("session_id"),
            user_role=record.get("user_role", "anonymous"),
            risk_level=record.get("risk_level", "low"),
            input_decision=record.get("input_decision", ""),
            output_decision=record.get("output_decision"),
            query_hash=record.get("query_hash", ""),
            timestamp=record.get("created_at", ""),
            workflow_stages=json.loads(record.get("workflow_stages") or "[]"),
            flags=json.loads(record.get("flags") or "[]"),
        ),
    )


@router.get(
    "/audit/export",
    summary="Export audit log as CSV",
    description="Compliance export of audit records. Query hash only — no raw text.",
)
async def audit_export(
    window_hours: int = Query(default=24, ge=1, le=8760),
) -> StreamingResponse:
    store = SQLiteStore()
    try:
        cutoff_expr = f"datetime('now', '-{window_hours} hours')"
        with store._get_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT audit_id, request_id, session_id, user_role, risk_level,
                       input_decision, output_decision, query_hash, workflow_stages,
                       flags, created_at
                FROM audit_log
                WHERE created_at > {cutoff_expr}
                ORDER BY created_at DESC
                """
            ).fetchall()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "AUDIT_EXPORT_FAILURE", "message": str(exc)},
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "audit_id", "request_id", "session_id", "user_role", "risk_level",
        "input_decision", "output_decision", "query_hash", "workflow_stages",
        "flags", "created_at",
    ])
    for row in rows:
        writer.writerow([
            row["audit_id"], row["request_id"], row["session_id"],
            row["user_role"], row["risk_level"], row["input_decision"],
            row["output_decision"], row["query_hash"], row["workflow_stages"],
            row["flags"], row["created_at"],
        ])

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=meditrust_audit.csv"},
    )
