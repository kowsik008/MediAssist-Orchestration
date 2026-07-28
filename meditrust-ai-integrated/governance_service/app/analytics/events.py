"""
governance_service/app/analytics/events.py
--------------------------------------------
KPI event definitions and property builders.

SECURITY RULE: No raw healthcare query text, no patient data, no names may
ever appear in event properties. Use hashed query IDs, role labels and
categorical metrics only.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional


class EventType(str, Enum):
    WORKFLOW_STARTED       = "meditrust_workflow_started"
    INPUT_GUARD_RESULT     = "meditrust_input_guard_result"
    CACHE_HIT              = "meditrust_cache_hit"
    CACHE_MISS             = "meditrust_cache_miss"
    RETRIEVAL_COMPLETED    = "meditrust_retrieval_completed"
    CONTEXT_OPTIMIZED      = "meditrust_context_optimized"
    LLM_INVOKED            = "meditrust_llm_invoked"
    OUTPUT_GUARD_RESULT    = "meditrust_output_guard_result"
    ANSWER_DELIVERED       = "meditrust_answer_delivered"
    ESCALATION_TRIGGERED   = "meditrust_escalation_triggered"
    FALLBACK_ACTIVATED     = "meditrust_fallback_activated"
    FEEDBACK_SUBMITTED     = "meditrust_feedback_submitted"
    ERROR_OCCURRED         = "meditrust_error_occurred"


# ---------------------------------------------------------------------------
# Property builders — one per event type
# These enforce the no-raw-text rule at construction time.
# ---------------------------------------------------------------------------

def build_workflow_started(
    request_id: str,
    session_id: Optional[str],
    user_role: str,
    query_hash: str,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "session_id": session_id or "anon",
        "user_role": user_role,
        "query_hash": query_hash,
    }


def build_input_guard_result(
    request_id: str,
    decision: str,
    risk_level: str,
    items_redacted: int,
    injection_detected: bool,
    guard_latency_ms: int,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "decision": decision,
        "risk_level": risk_level,
        "items_redacted": items_redacted,
        "injection_detected": injection_detected,
        "guard_latency_ms": guard_latency_ms,
    }


def build_cache_hit(
    request_id: str,
    cache_latency_ms: int,
    ttl_remaining_s: Optional[int] = None,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "cache_latency_ms": cache_latency_ms,
        "ttl_remaining_s": ttl_remaining_s,
    }


def build_cache_miss(request_id: str) -> Dict[str, Any]:
    return {"request_id": request_id}


def build_retrieval_completed(
    request_id: str,
    num_docs_retrieved: int,
    retrieval_latency_ms: int,
    precision_at_3: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "num_docs_retrieved": num_docs_retrieved,
        "retrieval_latency_ms": retrieval_latency_ms,
        "precision_at_3": precision_at_3,
    }


def build_context_optimized(
    request_id: str,
    tokens_before: int,
    tokens_after: int,
    tokens_saved: int,
    method: str,
) -> Dict[str, Any]:
    reduction_pct = round((tokens_saved / max(tokens_before, 1)) * 100, 1)
    return {
        "request_id": request_id,
        "tokens_before": tokens_before,
        "tokens_after": tokens_after,
        "tokens_saved": tokens_saved,
        "reduction_pct": reduction_pct,
        "method": method,
    }


def build_llm_invoked(
    request_id: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    llm_latency_ms: int,
    invocation_count: int = 1,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "llm_latency_ms": llm_latency_ms,
        "invocation_count": invocation_count,
    }


def build_output_guard_result(
    request_id: str,
    decision: str,
    citation_validity_pct: float,
    grounding_score: float,
    schema_valid: bool,
    safety_passed: bool,
    guard_latency_ms: int,
    failure_count: int,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "decision": decision,
        "citation_validity_pct": round(citation_validity_pct, 2),
        "grounding_score": round(grounding_score, 4),
        "schema_valid": schema_valid,
        "safety_passed": safety_passed,
        "guard_latency_ms": guard_latency_ms,
        "failure_count": failure_count,
    }


def build_answer_delivered(
    request_id: str,
    total_latency_ms: int,
    cache_hit: bool,
    risk_level: str,
    validation_status: str,
    requires_human_review: bool,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "total_latency_ms": total_latency_ms,
        "cache_hit": cache_hit,
        "risk_level": risk_level,
        "validation_status": validation_status,
        "requires_human_review": requires_human_review,
    }


def build_escalation_triggered(
    request_id: str,
    reason: str,
    stage: str,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "reason": reason,
        "stage": stage,
    }


def build_fallback_activated(
    request_id: str,
    component: str,
    fallback_mode: str,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "component": component,
        "fallback_mode": fallback_mode,
    }


def build_feedback_submitted(
    request_id: str,
    original_request_id: str,
    rating: int,
    helpful: bool,
    user_role: str,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "original_request_id": original_request_id,
        "rating": rating,
        "helpful": helpful,
        "user_role": user_role,
    }


def build_error_occurred(
    request_id: str,
    error_code: str,
    component: str,
    stage: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "request_id": request_id,
        "error_code": error_code,
        "component": component,
        "stage": stage,
    }
