from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class WorkflowRequest(BaseModel):
    schema_version: str = "1.0"
    request_id: str = Field(default_factory=lambda: f"REQ-{uuid4().hex[:12].upper()}")
    query: str = Field(min_length=1, max_length=4096)
    user_role: Literal[
        "doctor",
        "nurse",
        "pharmacist",
        "compliance_officer",
        "administrator",
        "public",
    ] = "public"
    mode: Literal["baseline", "optimized"] = "optimized"
    session_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    status_filter: str = "active"
    source_type: str | None = None
    document_ids: list[str] | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    role: str = "public"
    top_k: int = Field(default=5, ge=1, le=20)
    status: str = "active"
    source_type: str | None = None
    document_ids: list[str] | None = None
    tags: list[str] | None = None


class FeedbackRequest(BaseModel):
    request_id: str
    rating: int = Field(ge=1, le=5)
    helpful: bool
    comment: str | None = Field(default=None, max_length=1024)
    user_role: str = "public"
