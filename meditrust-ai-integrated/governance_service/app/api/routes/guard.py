"""
governance_service/app/api/routes/guard.py
--------------------------------------------
POST /api/v1/guard/input   — Input guardrail endpoint
POST /api/v1/guard/output  — Output guardrail endpoint

Called by:
  - Member 2 (Orchestration) LangGraph nodes: input_guard, validate_response
  - Member 4 (Gateway) before forwarding to orchestration

Both endpoints are synchronous (blocking) because guardrails must complete
before any downstream processing.
"""

from __future__ import annotations

import time
from typing import List, Optional, Set

from fastapi import APIRouter, Body, HTTPException, status

from governance_service.app.analytics.adapter import analytics_adapter
from governance_service.app.analytics.events import (
    EventType,
    build_input_guard_result,
    build_output_guard_result,
    build_escalation_triggered,
)
from governance_service.app.config import settings
from governance_service.app.core.input_guard import run_input_guard
from governance_service.app.core.output_guard import run_output_guard
from governance_service.app.utils.id_generator import (
    hash_query,
    new_audit_id,
    new_request_id,
)
from governance_service.app.utils.logger import get_logger

# Import shared schemas (used by all modules)
from shared.schemas.governance import (
    CitationCheckResult,
    GroundingCheckResult as GroundingCheckSchema,
    GuardDecision,
    InputGuardRequest,
    InputGuardResponse,
    InjectionFinding,
    OutputGuardRequest,
    OutputGuardResponse,
    RedactionSummary,
    RiskLevel,
    ValidationStatus,
)

log = get_logger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# POST /guard/input
# ---------------------------------------------------------------------------

@router.post(
    "/guard/input",
    response_model=InputGuardResponse,
    summary="Screen and classify an incoming query",
    description=(
        "Applies redaction, injection detection, risk classification and role "
        "checks. Returns a GuardDecision and sanitised safe_query."
    ),
)
async def guard_input(request: InputGuardRequest = Body(...)) -> InputGuardResponse:
    log.info(
        "Input guard request received",
        extra={
            "request_id": request.request_id,
            "user_role": request.user_role,
            "query_len": len(request.query),
        },
    )

    try:
        result = run_input_guard(
            query=request.query,
            user_role=request.user_role,
            conversation_history=request.conversation_history,
        )
    except Exception as exc:
        log.error("Input guard engine failure", extra={"error": str(exc)})
        if settings.GUARDRAILS_DEGRADED_FALLBACK:
            # Deterministic fallback: allow with warning
            result = _degraded_input_allow(request.query)
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error_code": "GUARDRAIL_FAILURE", "message": str(exc)},
            )

    # ── Emit KPI event ────────────────────────────────────────────────────────
    is_injection = result.decision == "block" and any(
        "injection" in f.pattern_matched.lower() for f in result.injection_findings
    )
    analytics_adapter.capture(
        event_type=EventType.INPUT_GUARD_RESULT,
        properties=build_input_guard_result(
            request_id=request.request_id,
            decision=result.decision,
            risk_level=result.risk_level,
            items_redacted=result.redaction.items_redacted if result.redaction else 0,
            injection_detected=is_injection,
            guard_latency_ms=result.guard_latency_ms,
        ),
        request_id=request.request_id,
        session_id=request.session_id,
        user_role=request.user_role,
    )

    # ── Write audit record ────────────────────────────────────────────────────
    analytics_adapter.write_audit(
        audit_id=new_audit_id(),
        request_id=request.request_id,
        query_hash=hash_query(request.query),
        input_decision=result.decision,
        risk_level=result.risk_level,
        session_id=request.session_id,
        user_role=request.user_role,
    )

    # ── Emit escalation event if needed ──────────────────────────────────────
    if result.requires_human_review:
        analytics_adapter.capture(
            event_type=EventType.ESCALATION_TRIGGERED,
            properties=build_escalation_triggered(
                request_id=request.request_id,
                reason=result.risk_reason,
                stage="input_guard",
            ),
            request_id=request.request_id,
            session_id=request.session_id,
            user_role=request.user_role,
        )

    # ── Build response ────────────────────────────────────────────────────────
    redaction_summary: Optional[RedactionSummary] = None
    if result.redaction and result.redaction.items_redacted > 0:
        redaction_summary = RedactionSummary(
            items_redacted=result.redaction.items_redacted,
            categories=result.redaction.categories,
            redacted_query=result.safe_query,
        )

    injection_findings: List[InjectionFinding] = [
        InjectionFinding(
            pattern_matched=f.pattern_matched,
            severity=f.severity,
            description=f.description,
        )
        for f in result.injection_findings
    ]

    return InputGuardResponse(
        request_id=request.request_id,
        decision=GuardDecision(result.decision),
        risk_level=RiskLevel(result.risk_level),
        risk_reason=result.risk_reason,
        redaction=redaction_summary,
        injection_findings=injection_findings,
        safe_query=result.safe_query,
        requires_human_review=result.requires_human_review,
        guard_latency_ms=result.guard_latency_ms,
        guardrail_mode=result.guardrail_mode,
    )


# ---------------------------------------------------------------------------
# POST /guard/output
# ---------------------------------------------------------------------------

@router.post(
    "/guard/output",
    response_model=OutputGuardResponse,
    summary="Validate LLM-generated answer before delivery",
    description=(
        "Validates schema, citations, grounding and safety. Returns a "
        "ValidationStatus decision and optionally strips or replaces the answer."
    ),
)
async def guard_output(request: OutputGuardRequest = Body(...)) -> OutputGuardResponse:
    log.info(
        "Output guard request received",
        extra={
            "request_id": request.request_id,
            "citation_count": len(request.citations),
            "retry_count": request.retry_count,
        },
    )

    # Convert Citation Pydantic models to plain dicts for the engine
    citations_dicts = [c.model_dump() for c in request.citations]
    retrieved_ids: Set[str] = set(request.retrieved_document_ids)

    # Extract retrieved_chunks from metadata if provided (Member 2 passes these)
    retrieved_chunks: List[str] = request.metadata.get("retrieved_chunks", [])

    try:
        result = run_output_guard(
            answer=request.answer,
            citations=citations_dicts,
            cautions=request.cautions,
            risk_level=request.risk_level,
            user_role=request.user_role,
            retrieved_document_ids=list(retrieved_ids),
            retrieved_chunks=retrieved_chunks,
            retry_count=request.retry_count,
        )
    except Exception as exc:
        log.error("Output guard engine failure", extra={"error": str(exc)})
        if settings.GUARDRAILS_DEGRADED_FALLBACK:
            result = _degraded_output_pass(request.answer, request.cautions)
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"error_code": "OUTPUT_GUARD_FAILURE", "message": str(exc)},
            )

    # ── Emit KPI event ────────────────────────────────────────────────────────
    citation_validity = (
        result.citation_result.validity_pct if result.citation_result else 100.0
    )
    grounding_score = (
        result.grounding_result.score if result.grounding_result else 1.0
    )

    analytics_adapter.capture(
        event_type=EventType.OUTPUT_GUARD_RESULT,
        properties=build_output_guard_result(
            request_id=request.request_id,
            decision=result.decision,
            citation_validity_pct=citation_validity,
            grounding_score=grounding_score,
            schema_valid=result.schema_valid,
            safety_passed=result.safety_passed,
            guard_latency_ms=result.guard_latency_ms,
            failure_count=len(result.failure_reasons),
        ),
        request_id=request.request_id,
        user_role=request.user_role,
    )

    if result.requires_human_review:
        analytics_adapter.capture(
            event_type=EventType.ESCALATION_TRIGGERED,
            properties=build_escalation_triggered(
                request_id=request.request_id,
                reason="; ".join(result.failure_reasons[:3]),
                stage="output_guard",
            ),
            request_id=request.request_id,
            user_role=request.user_role,
        )

    # ── Build response ────────────────────────────────────────────────────────
    citation_checks: List[CitationCheckResult] = []
    if result.citation_result:
        citation_checks = [
            CitationCheckResult(
                document_id=c.document_id,
                passed=c.passed,
                failure_reason=c.failure_reason if not c.passed else None,
            )
            for c in result.citation_result.checks
        ]

    grounding_schema: Optional[GroundingCheckSchema] = None
    if result.grounding_result:
        grounding_schema = GroundingCheckSchema(
            score=result.grounding_result.score,
            passed=result.grounding_result.passed,
            unsupported_claims=result.grounding_result.unsupported_claims,
            method=result.grounding_result.method,
        )

    return OutputGuardResponse(
        request_id=request.request_id,
        decision=ValidationStatus(result.decision),
        answer=result.answer,
        cautions=result.cautions,
        citation_checks=citation_checks,
        grounding_check=grounding_schema,
        schema_valid=result.schema_valid,
        safety_passed=result.safety_passed,
        failure_reasons=result.failure_reasons,
        requires_human_review=result.requires_human_review,
        guard_latency_ms=result.guard_latency_ms,
        guardrail_mode=result.guardrail_mode,
    )


# ---------------------------------------------------------------------------
# Degraded-mode helpers
# ---------------------------------------------------------------------------

def _degraded_input_allow(query: str):
    """Minimal safe allow when the guardrail engine itself fails."""
    from governance_service.app.core.input_guard import InputGuardResult
    return InputGuardResult(
        decision="warn",
        risk_level="medium",
        risk_reason="Guardrails running in degraded mode — deterministic engine unavailable.",
        safe_query=query,
        guardrail_mode="degraded",
        failure_reasons=["Guardrail engine exception — degraded fallback active."],
    )


def _degraded_output_pass(answer: str, cautions: List[str]):
    """Minimal pass-with-warning when the output guard engine fails."""
    from governance_service.app.core.output_guard import OutputGuardResult
    return OutputGuardResult(
        decision="pass_with_warning",
        answer=answer,
        cautions=[
            *cautions,
            "Output validation ran in degraded mode — results may be unverified.",
        ],
        guardrail_mode="degraded",
        failure_reasons=["Output guard engine exception — degraded fallback active."],
    )
