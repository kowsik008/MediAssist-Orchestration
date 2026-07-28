"""
shared/schemas/common.py
------------------------
Shared Pydantic base models and common types used across ALL MediTrust AI
modules (Member 1 Knowledge, Member 2 Orchestration, Member 3 Governance,
Member 4 Integration/Frontend).

Every service imports from here so the contract stays frozen in one place.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Enumerations (shared across all services)
# ---------------------------------------------------------------------------


class RiskLevel(str, Enum):
    """Governs routing in the LangGraph flow."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceStatus(str, Enum):
    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    UNAVAILABLE = "unavailable"


class ValidationStatus(str, Enum):
    PASS = "pass"
    PASS_WITH_WARNING = "pass_with_warning"
    REGENERATE = "regenerate"
    ESCALATE = "escalate"
    BLOCK = "block"


class SourceType(str, Enum):
    PUBLIC = "public"          # CDC, WHO, etc.
    SYNTHETIC = "synthetic"    # Demo-only SOPs


class DocumentStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    DRAFT = "draft"


class UserRole(str, Enum):
    DOCTOR = "doctor"
    NURSE = "nurse"
    PHARMACIST = "pharmacist"
    COMPLIANCE_OFFICER = "compliance_officer"
    ADMINISTRATOR = "administrator"
    ANONYMOUS = "anonymous"


class GuardDecision(str, Enum):
    ALLOW = "allow"
    REDACT = "redact"
    WARN = "warn"
    ESCALATE = "escalate"
    BLOCK = "block"


class AnalyticsBackend(str, Enum):
    POSTHOG = "posthog"
    SQLITE = "sqlite"
    JSONL = "jsonl"


# ---------------------------------------------------------------------------
# Shared base models
# ---------------------------------------------------------------------------


class BaseRequest(BaseModel):
    """Every inbound request carries a correlation ID and timestamp."""

    schema_version: str = Field(default=SCHEMA_VERSION)
    request_id: str = Field(
        default_factory=lambda: f"REQ-{uuid.uuid4().hex[:12].upper()}"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"populate_by_name": True, "use_enum_values": True}


class BaseResponse(BaseModel):
    """Every outbound response echoes the request ID and schema version."""

    schema_version: str = Field(default=SCHEMA_VERSION)
    request_id: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"populate_by_name": True, "use_enum_values": True}


# ---------------------------------------------------------------------------
# Citation model (used by Member 1 Knowledge + Member 3 Governance)
# ---------------------------------------------------------------------------


class Citation(BaseModel):
    document_id: str = Field(..., description="Unique doc ID e.g. CDC-IPC-001")
    title: str
    section: Optional[str] = None
    publisher: str
    url: Optional[str] = None
    source_type: SourceType = SourceType.PUBLIC
    status: DocumentStatus = DocumentStatus.ACTIVE
    version_date: Optional[str] = None
    access_roles: List[UserRole] = Field(default_factory=list)
    licence: Optional[str] = None
    is_synthetic: bool = False


# ---------------------------------------------------------------------------
# Token metrics (used by Member 2 Orchestration + Member 3 Governance)
# ---------------------------------------------------------------------------


class TokenMetrics(BaseModel):
    tokens_before_optimization: int = 0
    tokens_after_optimization: int = 0
    tokens_saved: int = 0
    optimization_method: str = "none"  # "headroom" | "deterministic" | "none"


# ---------------------------------------------------------------------------
# Latency metrics (used by all services)
# ---------------------------------------------------------------------------


class LatencyMetrics(BaseModel):
    total_latency_ms: int = 0
    guard_latency_ms: int = 0
    retrieval_latency_ms: int = 0
    llm_latency_ms: int = 0
    cache_latency_ms: int = 0


# ---------------------------------------------------------------------------
# Workflow trace event (used by Member 2 + Member 3)
# ---------------------------------------------------------------------------


class WorkflowTraceEvent(BaseModel):
    stage: str
    status: str                         # "started" | "completed" | "skipped" | "failed"
    latency_ms: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# ---------------------------------------------------------------------------
# Health check models (used by ALL services)
# ---------------------------------------------------------------------------


class DependencyHealth(BaseModel):
    name: str
    status: str          # "ok" | "degraded" | "unavailable"
    mode: str            # "integrated" | "mock" | "fallback"
    latency_ms: Optional[int] = None
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    service: str
    status: str          # "healthy" | "degraded" | "unhealthy"
    version: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    dependencies: List[DependencyHealth] = Field(default_factory=list)
    uptime_seconds: Optional[float] = None


# ---------------------------------------------------------------------------
# Error models
# ---------------------------------------------------------------------------


class ServiceError(BaseModel):
    error_code: str
    message: str
    request_id: Optional[str] = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    detail: Optional[Dict[str, Any]] = None
