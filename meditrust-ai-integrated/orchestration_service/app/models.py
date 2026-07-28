from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PromptVersion(str, Enum):
    baseline_v1 = "baseline_v1"
    optimized_v1 = "optimized_v1"


class InvocationMode(str, Enum):
    baseline = "baseline"
    optimized = "optimized"


class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class IntentType(str, Enum):
    general_info = "general_info"
    hospital_process = "hospital_process"
    medication_question = "medication_question"
    diagnosis_or_treatment = "diagnosis_or_treatment"
    emergency = "emergency"
    unknown = "unknown"


class ClassificationReason(BaseModel):
    label: str
    score: float
    rule: str


class SourceSnippet(BaseModel):
    source_id: str
    title: str
    section: str
    version: str = "current"
    content: str
    status: str = "active"
    roles_allowed: list[str] = Field(default_factory=lambda: ["public"])


class InvocationRequest(BaseModel):
    query: str = Field(min_length=1, max_length=6000)
    user_role: str = Field(default="public")
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str | None = None
    source_snippets: list[SourceSnippet] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=20)
    status_filter: str = "active"
    source_type: str | None = None
    document_ids: list[str] | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClassificationResult(BaseModel):
    intent: IntentType
    risk: RiskLevel
    ambiguous: bool = False
    used_gemini: bool = False
    reasons: list[ClassificationReason] = Field(default_factory=list)


class OptimizedContext(BaseModel):
    snippets: list[SourceSnippet] = Field(default_factory=list)
    strategy: str
    headroom_used: bool
    token_count_before: int
    token_count_after: int
    warnings: list[str] = Field(default_factory=list)
    negative_statements: list[str] = Field(default_factory=list)
    escalation_text: str | None = None


class TraceEvent(BaseModel):
    timestamp: str = Field(default_factory=utc_now_iso)
    event_type: str
    node: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class GraphNodeDefinition(BaseModel):
    name: str
    description: str


class GraphEdgeDefinition(BaseModel):
    source: str
    target: str
    condition: str = "always"


class ProviderResponse(BaseModel):
    answer: str
    warnings: list[str] = Field(default_factory=list)
    negative_statements: list[str] = Field(default_factory=list)
    escalation_text: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    raw: dict[str, Any] = Field(default_factory=dict)


class InvocationMetrics(BaseModel):
    latency_ms: int = 0
    provider_latency_ms: int = 0
    model_invocation_count: int = 0
    token_count_before: int = 0
    token_count_after: int = 0


class GraphDecision(BaseModel):
    should_escalate: bool = False
    should_regenerate: bool = False
    final_status: str = "completed"
    rationale: str = ""


class GraphState(BaseModel):
    request: InvocationRequest
    mode: InvocationMode
    prompt_version: PromptVersion
    classification: ClassificationResult | None = None
    input_guard_decision: str | None = None
    input_guard_risk_level: str | None = None
    input_guard_reason: str | None = None
    output_guard_decision: str | None = None
    output_guard_failure_reasons: list[str] = Field(default_factory=list)
    retrieved_document_ids: list[str] = Field(default_factory=list)
    retrieved_citations: list[dict[str, Any]] = Field(default_factory=list)
    cache_hit: bool = False
    cache_answer: str | None = None
    cache_citations: list[dict[str, Any]] = Field(default_factory=list)
    evidence_status: str | None = None
    leakage_detected: bool = False
    optimized_context: OptimizedContext | None = None
    provider_response: ProviderResponse | None = None
    metrics: InvocationMetrics = Field(default_factory=InvocationMetrics)
    trace: list[TraceEvent] = Field(default_factory=list)
    regeneration_count: int = 0
    decision: GraphDecision = Field(default_factory=GraphDecision)


class InvocationResponse(BaseModel):
    request_id: str
    mode: InvocationMode
    prompt_version: PromptVersion
    answer: str
    classification: ClassificationResult
    source_ids: list[str]
    citations: list[dict[str, Any]] = Field(default_factory=list)
    evidence_status: str | None = None
    cache_hit: bool = False
    warnings: list[str] = Field(default_factory=list)
    negative_statements: list[str] = Field(default_factory=list)
    escalation_text: str | None = None
    metrics: InvocationMetrics
    trace: list[TraceEvent]
    final_status: str


class HealthResponse(BaseModel):
    status: str
    environment: str
    provider: str
    knowledge_service_base_url: str
    governance_service_base_url: str
    headroom_enabled: bool
    headroom_available: bool
    headroom_base_url: str | None = None


class ExampleResponse(BaseModel):
    requests: list[dict[str, Any]]
    responses: list[dict[str, Any]]
