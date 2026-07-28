from __future__ import annotations

from typing import Any

import httpx

from orchestration_service.app.config import Settings
from orchestration_service.app.models import SourceSnippet


class KnowledgeServiceClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def health(self) -> dict[str, Any]:
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.get(f"{self.settings.knowledge_service_base_url}/health")
            response.raise_for_status()
            return response.json()

    def cache_lookup(self, *, query: str, role: str, status: str) -> dict[str, Any]:
        payload = {
            "query": query,
            "role": role,
            "filters": {
                "status": status,
            },
        }
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.post(f"{self.settings.knowledge_service_base_url}/cache/lookup", json=payload)
            response.raise_for_status()
            return response.json()

    def retrieve(
        self,
        *,
        query: str,
        role: str,
        top_k: int,
        status: str,
        source_type: str | None,
        document_ids: list[str] | None,
        tags: list[str] | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "query": query,
            "role": role,
            "top_k": top_k,
            "status": status,
        }
        if source_type:
            payload["source_type"] = source_type
        if document_ids:
            payload["document_ids"] = document_ids
        if tags:
            payload["tags"] = tags

        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.post(f"{self.settings.knowledge_service_base_url}/retrieve", json=payload)
            response.raise_for_status()
            return response.json()

    def cache_write(
        self,
        *,
        query: str,
        role: str,
        status: str,
        answer: str,
        citations: list[dict[str, Any]],
        validation_status: str,
    ) -> dict[str, Any]:
        source_versions = {
            str(citation.get("document_id")): str(citation.get("version_date"))
            for citation in citations
            if citation.get("document_id") and citation.get("version_date")
        }
        payload = {
            "query": query,
            "role": role,
            "filters": {"status": status},
            "answer": answer,
            "citations": citations,
            "validation_status": validation_status,
            "source_versions": source_versions,
        }
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.post(
                f"{self.settings.knowledge_service_base_url}/cache/write",
                json=payload,
            )
            response.raise_for_status()
            return response.json()


def retrieved_chunks_to_snippets(results: list[dict[str, Any]]) -> list[SourceSnippet]:
    snippets: list[SourceSnippet] = []
    for result in results:
        metadata = result.get("metadata", {})
        citation = result.get("citation", {})
        access_roles = metadata.get("access_roles", "public")
        if isinstance(access_roles, str):
            roles_allowed = [item.strip() for item in access_roles.split(",") if item.strip()]
        else:
            roles_allowed = list(access_roles or ["public"])
        snippets.append(
            SourceSnippet(
                source_id=result.get("chunk_id", ""),
                title=result.get("title", ""),
                section=result.get("section", ""),
                version=str(citation.get("version_date", metadata.get("version_date", "current"))),
                content=result.get("text", ""),
                status=str(metadata.get("status", "active")),
                roles_allowed=roles_allowed,
            )
        )
    return snippets


def extract_document_ids(results: list[dict[str, Any]]) -> list[str]:
    seen: list[str] = []
    for result in results:
        document_id = result.get("document_id")
        if isinstance(document_id, str) and document_id and document_id not in seen:
            seen.append(document_id)
    return seen


def extract_citations(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for result in results:
        citation = result.get("citation")
        metadata = result.get("metadata", {})
        if isinstance(citation, dict):
            merged = dict(citation)
            if "status" not in merged and "status" in metadata:
                merged["status"] = metadata["status"]
            if "access_roles" not in merged and "access_roles" in metadata:
                merged["access_roles"] = metadata["access_roles"]
            if "publisher" not in merged and "publisher" in metadata:
                merged["publisher"] = metadata["publisher"]
            if "title" not in merged and "title" in metadata:
                merged["title"] = metadata["title"]
            citations.append(merged)
    return citations
