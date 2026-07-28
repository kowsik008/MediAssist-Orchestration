"""
shared/schemas/governance.py
-----------------------------
Governance-specific request/response schemas that other modules (Member 1,
Member 2, Member 4) import when calling the Governance Service APIs.

INTEGRATION GUIDE
-----------------
Member 1 (Knowledge):
    from shared.schemas.governance import InputGuardRequest, InputGuardResponse
    # Call POST http://localhost:8002/api/v1/guard/input before retrieval

Member 2 (Orchestration):
    from shared.schemas.governance import (
        InputGuardRequest, InputGuardResponse,
        OutputGuardRequest, OutputGuardResponse,
        AnalyticsCaptureRequest,
    )

Member 4 (Integration Gateway):
    from shared.schemas.governance import MetricsSummaryResponse, FeedbackRequest
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from shared.schemas.common import (
    BaseRequest,
    BaseResponse,
    Citation,
    GuardDecision,
    LatencyMetrics,
    RiskLevel,
    TokenMetrics,
    UserRole,
    ValidationStatus,
)


# ---------------------------------------------------------------------------
# Input Guard
# ---------------------------------------------------------------------------


class InjectionFinding(BaseModel):
    pattern_matched: str
    severity: str      # "low" | "medium" | "high"
    description: str


class RedactionSummary(BaseModel):
    items_redacted: int
    categories: List[str]   # e.g. ["patient_id", "ssn", "dob"]
    redacted_query: str      # Safe version with [REDACTED] placeholders


class InputGuardRequest(BaseRequest):
    """
    Sent by Member 2 (Orchestration) or Member 4 (Gateway) before any
    retrieval or LLM call takes place.
    """

    query: str = Field(..., min_length=1, max_length=4096)
    user_role: UserRole = UserRole.ANONYMOUS
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class InputGuardResponse(BaseResponse):
    """
    Returned to the caller after input screening.
    decision == "allow"    → proceed to retrieval
    decision == "redact"   → use redacted_query, log warning
    decision == "escalate" → route to human_escalation node
    decision == "block"    → stop, return safe message to user
    """

    decision: GuardDecision
    risk_level: RiskLevel
    risk_reason: Optional[str] = None
    redaction: Optional[RedactionSummary] = None
    injection_findings: List[InjectionFinding] = Field(default_factory=list)
    safe_query: str = Field(..., description="Sanitised query safe to use downstream")
    requires_human_review: bool = False
    guard_latency_ms: int = 0
    guardrail_mode: str = "deterministic"   # "deterministic" | "degraded"


# ---------------------------------------------------------------------------
# Output Guard
# ---------------------------------------------------------------------------


class CitationCheckResult(BaseModel):
    document_id: str
    passed: bool
    failure_reason: Optional[str] = None


class GroundingCheckResult(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    unsupported_claims: List[str] = Field(default_factory=list)
    method: str = "deterministic"    # "deterministic" | "gemini_verifier"


class OutputGuardRequest(BaseRequest):
    """
    Sent by Member 2 (Orchestration) after LLM generation, before
    caching or returning the answer to the user.
    """

    answer: str
    cautions: List[str] = Field(default_factory=list)
    citations: List[Citation]
    risk_level: RiskLevel = RiskLevel.LOW
    user_role: UserRole = UserRole.ANONYMOUS
    retrieved_document_ids: List[str] = Field(
        default_factory=list,
        description="IDs actually retrieved from Chroma — used for citation cross-check",
    )
    token_metrics: Optional[TokenMetrics] = None
    retry_count: int = Field(default=0, ge=0, le=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OutputGuardResponse(BaseResponse):
    """
    decision == "pass"              → cache and return answer
    decision == "pass_with_warning" → return answer + caution banner
    decision == "regenerate"        → orchestration should retry once
    decision == "escalate"          → route to human_escalation
    decision == "block"             → withhold answer, return safe message
    """

    decision: ValidationStatus
    answer: Optional[str] = Field(
        None,
        description="May be stripped or replaced with a safe message if blocked",
    )
    cautions: List[str] = Field(default_factory=list)
    citation_checks: List[CitationCheckResult] = Field(default_factory=list)
    grounding_check: Optional[GroundingCheckResult] = None
    schema_valid: bool = True
    safety_passed: bool = True
    failure_reasons: List[str] = Field(default_factory=list)
    requires_human_review: bool = False
    guard_latency_ms: int = 0
    guardrail_mode: str = "deterministic"


# ---------------------------------------------------------------------------
# Analytics / KPI
# ---------------------------------------------------------------------------


class AnalyticsEventType(str, Enum):
    WORKFLOW_STARTED = "meditrust_workflow_started"
    INPUT_GUARD_RESULT = "meditrust_input_guard_result"
    CACHE_HIT = "meditrust_cache_hit"
    CACHE_MISS = "meditrust_cache_miss"
    RETRIEVAL_COMPLETED = "meditrust_retrieval_completed"
    CONTEXT_OPTIMIZED = "meditrust_context_optimized"
    LLM_INVOKED = "meditrust_llm_invoked"
    OUTPUT_GUARD_RESULT = "meditrust_output_guard_result"
    ANSWER_DELIVERED = "meditrust_answer_delivered"
    ESCALATION_TRIGGERED = "meditrust_escalation_triggered"
    FALLBACK_ACTIVATED = "meditrust_fallback_activated"
    FEEDBACK_SUBMITTED = "meditrust_feedback_submitted"
    ERROR_OCCURRED = "meditrust_error_occurred"


class AnalyticsCaptureRequest(BaseRequest):
    """
    Sent by ANY module to record a KPI event.
    Raw healthcare text must NEVER appear in properties.
    """

    event_type: AnalyticsEventType
    session_id: Optional[str] = None
    user_role: UserRole = UserRole.ANONYMOUS
    properties: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Structured KPI data only — no raw query text, no patient data. "
            "Use hashed/anonymised identifiers."
        ),
    )
    token_metrics: Optional[TokenMetrics] = None
    latency_metrics: Optional[LatencyMetrics] = None


class AnalyticsCaptureResponse(BaseResponse):
    stored: bool
    backend_used: str   # "posthog" | "sqlite" | "jsonl"
    event_id: str


# ---------------------------------------------------------------------------
# Metrics summary
# ---------------------------------------------------------------------------


class GuardrailStats(BaseModel):
    total_requests: int = 0
    allowed: int = 0
    blocked: int = 0
    escalated: int = 0
    redacted: int = 0
    injection_attempts: int = 0
    high_risk_queries: int = 0


class RetrievalStats(BaseModel):
    total_retrievals: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    precision_at_3: Optional[float] = None
    avg_retrieval_latency_ms: Optional[float] = None


class TokenStats(BaseModel):
    total_tokens_before: int = 0
    total_tokens_after: int = 0
    total_tokens_saved: int = 0
    avg_reduction_pct: Optional[float] = None


class MetricsSummaryResponse(BaseResponse):
    """GET /api/v1/metrics/summary — consumed by Member 4 dashboard."""

    window_hours: int = 24
    guardrail_stats: GuardrailStats = Field(default_factory=GuardrailStats)
    retrieval_stats: RetrievalStats = Field(default_factory=RetrievalStats)
    token_stats: TokenStats = Field(default_factory=TokenStats)
    analytics_backend: str = "sqlite"
    total_llm_calls: int = 0
    total_escalations: int = 0
    avg_total_latency_ms: Optional[float] = None
    citation_validity_pct: Optional[float] = None
    unsupported_claim_pct: Optional[float] = None


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------


class FeedbackRequest(BaseRequest):
    """Submitted by user via Next.js UI (Member 4)."""

    original_request_id: str
    rating: int = Field(..., ge=1, le=5)
    helpful: bool
    comment: Optional[str] = Field(None, max_length=1024)
    user_role: UserRole = UserRole.ANONYMOUS


class FeedbackResponse(BaseResponse):
    stored: bool
    message: str = "Thank you for your feedback."


# ---------------------------------------------------------------------------
# Audit trace
# ---------------------------------------------------------------------------


class AuditTraceRequest(BaseRequest):
    """Member 2 / Member 4 can query the audit log for a specific request."""

    target_request_id: str
    include_redacted: bool = False   # Compliance officer only


class AuditRecord(BaseModel):
    audit_id: str
    request_id: str
    session_id: Optional[str]
    user_role: str
    risk_level: str
    input_decision: str
    output_decision: Optional[str]
    query_hash: str     # SHA-256 of original query — never the raw text
    timestamp: str
    workflow_stages: List[str] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)


class AuditTraceResponse(BaseResponse):
    record: Optional[AuditRecord] = None
    found: bool = False
