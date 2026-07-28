from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod

import httpx

from orchestration_service.app.config import Settings
from orchestration_service.app.models import (
    ClassificationResult,
    IntentType,
    ProviderResponse,
    RiskLevel,
    SourceSnippet,
)


def _build_evidence_block(snippets: list[SourceSnippet]) -> str:
    lines: list[str] = []
    for snippet in snippets:
        lines.append(
            f"[{snippet.source_id}] {snippet.title} | {snippet.section} | v={snippet.version}\n{snippet.content}"
        )
    return "\n\n".join(lines)


class BaseProvider(ABC):
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        query: str,
        snippets: list[SourceSnippet],
        classification: ClassificationResult,
    ) -> ProviderResponse:
        raise NotImplementedError

    def classify_ambiguous(self, query: str) -> ClassificationResult:
        return ClassificationResult(
            intent=IntentType.unknown,
            risk=RiskLevel.medium,
            ambiguous=True,
            used_gemini=False,
        )


class MockProvider(BaseProvider):
    def generate(
        self,
        system_prompt: str,
        query: str,
        snippets: list[SourceSnippet],
        classification: ClassificationResult,
    ) -> ProviderResponse:
        source_ids = [snippet.source_id for snippet in snippets]
        evidence = "; ".join(f"{snippet.title} ({snippet.source_id})" for snippet in snippets[:3])
        answer = (
            f"Mock response for '{query}'. "
            f"Intent={classification.intent.value}, risk={classification.risk.value}. "
            f"Evidence considered: {evidence or 'none provided'}."
        )
        warnings = ["Demonstration response from MockProvider."]
        negative = []
        escalation = None
        if classification.risk == RiskLevel.high:
            warnings.append("High-risk request detected.")
            escalation = "Escalate to a qualified clinician or hospital supervisor."
            negative.append("No diagnosis or treatment recommendation is being provided.")
        return ProviderResponse(
            answer=answer,
            warnings=warnings,
            negative_statements=negative,
            escalation_text=escalation,
            source_ids=source_ids,
            raw={"provider": "mock", "system_prompt_preview": system_prompt[:80]},
        )

    def classify_ambiguous(self, query: str) -> ClassificationResult:
        lowered = query.lower()
        if "pain" in lowered or "medicine" in lowered:
            return ClassificationResult(
                intent=IntentType.medication_question,
                risk=RiskLevel.medium,
                ambiguous=False,
                used_gemini=True,
            )
        return ClassificationResult(
            intent=IntentType.general_info,
            risk=RiskLevel.low,
            ambiguous=False,
            used_gemini=True,
        )


class UnavailableProvider(BaseProvider):
    def generate(
        self,
        system_prompt: str,
        query: str,
        snippets: list[SourceSnippet],
        classification: ClassificationResult,
    ) -> ProviderResponse:
        return ProviderResponse(
            answer="Model provider is unavailable. Please retry after restoring the configured provider.",
            warnings=["Provider unavailable."],
            negative_statements=["No generated answer could be produced."],
            escalation_text="Escalate to manual review if the request is time-sensitive.",
            source_ids=[snippet.source_id for snippet in snippets],
            raw={"provider": "unavailable"},
        )


class OpenAIProvider(BaseProvider):
    def __init__(self, settings: Settings):
        self.settings = settings

    def _invoke(self, instructions: str, input_text: str) -> tuple[str, dict]:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        body = {
            "model": self.settings.openai_model,
            "instructions": instructions,
            "input": input_text,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.settings.openai_base_url.rstrip('/')}/responses"
        with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
            response = client.post(url, headers=headers, json=body)
            response.raise_for_status()
            payload = response.json()
        return _extract_openai_text(payload), payload

    def generate(
        self,
        system_prompt: str,
        query: str,
        snippets: list[SourceSnippet],
        classification: ClassificationResult,
    ) -> ProviderResponse:
        source_ids = [snippet.source_id for snippet in snippets]
        input_text = (
            f"Classification: intent={classification.intent.value}, risk={classification.risk.value}\n\n"
            f"Evidence:\n{_build_evidence_block(snippets)}\n\n"
            f"User query:\n{query}"
        )
        start = time.perf_counter()
        try:
            text, payload = self._invoke(system_prompt, input_text)
        except Exception as exc:  # noqa: BLE001
            return ProviderResponse(
                answer="OpenAI invocation failed. Please retry after checking provider availability.",
                warnings=[f"OpenAI error: {exc.__class__.__name__}"],
                negative_statements=["No generated answer could be validated."],
                escalation_text="Escalate to manual review if the request is high-risk.",
                source_ids=source_ids,
                raw={"provider": "openai", "error": str(exc)},
            )

        latency_ms = int((time.perf_counter() - start) * 1000)
        return ProviderResponse(
            answer=text or "OpenAI returned an empty response.",
            warnings=[],
            negative_statements=[],
            escalation_text=None,
            source_ids=source_ids,
            raw={"provider": "openai", "latency_ms": latency_ms, "response_id": payload.get("id")},
        )

    def classify_ambiguous(self, query: str) -> ClassificationResult:
        instructions = (
            "Classify the healthcare support query. Return only a JSON object with keys "
            "intent, risk, and ambiguous. Allowed intents: general_info, hospital_process, "
            "medication_question, diagnosis_or_treatment, emergency, unknown. "
            "Allowed risks: low, medium, high."
        )
        try:
            text, _ = self._invoke(instructions, query)
            parsed = json.loads(_strip_json_fence(text))
            return ClassificationResult(
                intent=IntentType(parsed.get("intent", "unknown")),
                risk=RiskLevel(parsed.get("risk", "medium")),
                ambiguous=bool(parsed.get("ambiguous", True)),
                used_gemini=False,
            )
        except Exception:  # noqa: BLE001
            return ClassificationResult(
                intent=IntentType.unknown,
                risk=RiskLevel.medium,
                ambiguous=True,
                used_gemini=False,
            )


class GeminiProvider(BaseProvider):
    def __init__(self, settings: Settings):
        self.settings = settings

    def generate(
        self,
        system_prompt: str,
        query: str,
        snippets: list[SourceSnippet],
        classification: ClassificationResult,
    ) -> ProviderResponse:
        if not self.settings.gemini_api_key:
            return UnavailableProvider().generate(system_prompt, query, snippets, classification)

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent?key={self.settings.gemini_api_key}"
        )
        body = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                f"{system_prompt}\n\n"
                                f"Classification: intent={classification.intent.value}, risk={classification.risk.value}\n\n"
                                f"Evidence:\n{_build_evidence_block(snippets)}\n\n"
                                f"User query:\n{query}"
                            )
                        }
                    ]
                }
            ]
        }

        start = time.perf_counter()
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                response = client.post(url, json=body)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:  # noqa: BLE001
            return ProviderResponse(
                answer="Gemini invocation failed. Please retry after checking provider availability.",
                warnings=[f"Gemini error: {exc.__class__.__name__}"],
                negative_statements=["No generated answer could be validated."],
                escalation_text="Escalate to manual review if the request is high-risk.",
                source_ids=[snippet.source_id for snippet in snippets],
                raw={"provider": "gemini", "error": str(exc)},
            )

        latency_ms = int((time.perf_counter() - start) * 1000)
        text = _extract_gemini_text(payload)
        return ProviderResponse(
            answer=text or "Gemini returned an empty response.",
            warnings=[],
            negative_statements=[],
            escalation_text=None,
            source_ids=[snippet.source_id for snippet in snippets],
            raw={"provider": "gemini", "latency_ms": latency_ms, "payload": payload},
        )

    def classify_ambiguous(self, query: str) -> ClassificationResult:
        if not self.settings.gemini_api_key:
            return ClassificationResult(
                intent=IntentType.unknown,
                risk=RiskLevel.medium,
                ambiguous=True,
                used_gemini=False,
            )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.gemini_model}:generateContent?key={self.settings.gemini_api_key}"
        )
        schema_prompt = (
            "Classify the healthcare support query. "
            "Return strict JSON with keys: intent, risk, ambiguous. "
            "Allowed intents: general_info, hospital_process, medication_question, diagnosis_or_treatment, emergency, unknown. "
            "Allowed risks: low, medium, high."
        )
        body = {"contents": [{"parts": [{"text": f"{schema_prompt}\n\nQuery: {query}"}]}]}
        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                response = client.post(url, json=body)
                response.raise_for_status()
                payload = response.json()
        except Exception:  # noqa: BLE001
            return ClassificationResult(
                intent=IntentType.unknown,
                risk=RiskLevel.medium,
                ambiguous=True,
                used_gemini=False,
            )

        text = _extract_gemini_text(payload)
        try:
            parsed = json.loads(text)
            return ClassificationResult(
                intent=IntentType(parsed.get("intent", "unknown")),
                risk=RiskLevel(parsed.get("risk", "medium")),
                ambiguous=bool(parsed.get("ambiguous", True)),
                used_gemini=True,
            )
        except Exception:  # noqa: BLE001
            return ClassificationResult(
                intent=IntentType.unknown,
                risk=RiskLevel.medium,
                ambiguous=True,
                used_gemini=True,
            )


def _extract_gemini_text(payload: dict) -> str:
    candidates = payload.get("candidates", [])
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    texts = [part.get("text", "") for part in parts if part.get("text")]
    return "\n".join(texts).strip()


def _extract_openai_text(payload: dict) -> str:
    if payload.get("output_text"):
        return str(payload["output_text"]).strip()
    texts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                texts.append(str(content["text"]))
    return "\n".join(texts).strip()


def _strip_json_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return stripped


def build_provider(settings: Settings) -> BaseProvider:
    provider_name = settings.model_provider.lower()
    if provider_name == "openai":
        return OpenAIProvider(settings)
    if provider_name == "gemini":
        return GeminiProvider(settings)
    if provider_name == "unavailable":
        return UnavailableProvider()
    return UnavailableProvider()
