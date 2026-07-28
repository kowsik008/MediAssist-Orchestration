from __future__ import annotations

from typing import Any

import httpx

from orchestration_service.app.config import Settings


class GovernanceServiceClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def health(self) -> dict[str, Any]:
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.get(f"{self.settings.governance_service_base_url}/api/v1/health")
            response.raise_for_status()
            return response.json()

    def input_guard(
        self,
        *,
        request_id: str,
        query: str,
        user_role: str,
        session_id: str | None,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "request_id": request_id,
            "query": query,
            "user_role": _normalize_user_role(user_role),
            "session_id": session_id,
            "conversation_history": [],
            "metadata": metadata,
        }
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.post(f"{self.settings.governance_service_base_url}/api/v1/guard/input", json=payload)
            response.raise_for_status()
            return response.json()

    def output_guard(
        self,
        *,
        request_id: str,
        answer: str,
        cautions: list[str],
        citations: list[dict[str, Any]],
        risk_level: str,
        user_role: str,
        retrieved_document_ids: list[str],
        retrieved_chunks: list[str],
        retry_count: int,
        token_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "request_id": request_id,
            "answer": answer,
            "cautions": cautions,
            "citations": citations,
            "risk_level": risk_level,
            "user_role": _normalize_user_role(user_role),
            "retrieved_document_ids": retrieved_document_ids,
            "retry_count": retry_count,
            "token_metrics": token_metrics,
            "metadata": {
                "retrieved_chunks": retrieved_chunks,
            },
        }
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.post(f"{self.settings.governance_service_base_url}/api/v1/guard/output", json=payload)
            response.raise_for_status()
            return response.json()

    def analytics_capture(
        self,
        *,
        request_id: str,
        event_type: str,
        user_role: str,
        session_id: str | None,
        properties: dict[str, Any],
        token_metrics: dict[str, Any] | None = None,
        latency_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "request_id": request_id,
            "event_type": event_type,
            "user_role": _normalize_user_role(user_role),
            "session_id": session_id,
            "properties": properties,
        }
        if token_metrics:
            payload["token_metrics"] = token_metrics
        if latency_metrics:
            payload["latency_metrics"] = latency_metrics
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.post(f"{self.settings.governance_service_base_url}/api/v1/analytics/capture", json=payload)
            response.raise_for_status()
            return response.json()


def knowledge_citation_to_governance(citation: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    source_type = "public"
    if str(citation.get("source_type", metadata.get("source_type", ""))) == "synthetic_sop":
        source_type = "synthetic"
    status = str(metadata.get("status", "active"))
    access_roles = metadata.get("access_roles", [])
    if isinstance(access_roles, str):
        access_roles = [role.strip() for role in access_roles.split(",") if role.strip()]
    return {
        "document_id": citation.get("document_id", metadata.get("document_id", "")),
        "title": citation.get("title", metadata.get("title", "")),
        "section": citation.get("section", metadata.get("section")),
        "publisher": citation.get("publisher", metadata.get("publisher", "")),
        "url": citation.get("url", metadata.get("url")),
        "source_type": source_type,
        "status": status,
        "version_date": citation.get("version_date", metadata.get("version_date")),
        "access_roles": [_normalize_user_role(role) for role in access_roles if role],
        "licence": metadata.get("license_terms"),
        "is_synthetic": bool(citation.get("synthetic", metadata.get("synthetic") in (True, "true", "True"))),
    }


def _normalize_user_role(role: str) -> str:
    if role == "public":
        return "anonymous"
    return role
