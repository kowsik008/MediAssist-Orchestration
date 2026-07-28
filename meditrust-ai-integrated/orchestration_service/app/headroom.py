from __future__ import annotations

import os
import subprocess
from shutil import which

import httpx

from orchestration_service.app.config import Settings
from orchestration_service.app.models import ClassificationResult, OptimizedContext, SourceSnippet


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


class HeadroomAdapter:
    def __init__(self, settings: Settings):
        self.settings = settings

    def optimize(
        self,
        snippets: list[SourceSnippet],
        classification: ClassificationResult,
    ) -> OptimizedContext:
        all_text = "\n".join(snippet.content for snippet in snippets)
        token_before = estimate_tokens(all_text)

        if self.settings.headroom_enabled:
            if self._ensure_proxy():
                optimized = self._compress_with_proxy(snippets, classification, token_before)
                if optimized is not None:
                    return optimized

        return deterministic_fallback_optimization(snippets, classification)

    def _ensure_proxy(self) -> bool:
        if self.settings.headroom_available and self._proxy_healthcheck():
            return True
        if not self.settings.headroom_auto_start:
            return False
        return self._start_proxy() and self._proxy_healthcheck()

    def _proxy_healthcheck(self) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{self.settings.headroom_base_url}/health")
                return response.status_code == 200
        except Exception:  # noqa: BLE001
            return False

    def _start_proxy(self) -> bool:
        cli_path = self._resolve_cli_path()
        if not cli_path:
            return False

        env = os.environ.copy()
        env["HEADROOM_API_KEY"] = self.settings.headroom_api_key
        env["HEADROOM_MODEL"] = self.settings.headroom_model
        if self.settings.headroom_target_api_url:
            env["HEADROOM_TARGET_API_URL"] = self.settings.headroom_target_api_url

        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        args = [
            cli_path,
            "proxy",
            "--host",
            self.settings.headroom_proxy_host,
            "--port",
            str(self.settings.headroom_proxy_port),
        ]
        try:
            subprocess.Popen(  # noqa: S603
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=env,
                creationflags=creationflags,
            )
            return True
        except Exception:  # noqa: BLE001
            return False

    def _resolve_cli_path(self) -> str | None:
        if os.path.isabs(self.settings.headroom_cli_path) and os.path.exists(self.settings.headroom_cli_path):
            return self.settings.headroom_cli_path
        return which(self.settings.headroom_cli_path)

    def _compress_with_proxy(
        self,
        snippets: list[SourceSnippet],
        classification: ClassificationResult,
        token_before: int,
    ) -> OptimizedContext | None:
        role = self.settings.headroom_default_role
        source_map = {snippet.source_id: snippet for snippet in snippets}
        items = [
            {
                "type": "text",
                "id": snippet.source_id,
                "title": snippet.title,
                "text": (
                    f"Section: {snippet.section}\n"
                    f"Version: {snippet.version}\n"
                    f"Status: {snippet.status}\n"
                    f"Roles: {', '.join(snippet.roles_allowed)}\n"
                    f"Content: {snippet.content}"
                ),
                "metadata": {
                    "source_id": snippet.source_id,
                    "section": snippet.section,
                    "version": snippet.version,
                    "status": snippet.status,
                    "roles_allowed": snippet.roles_allowed,
                },
            }
            for snippet in snippets
        ]
        payload = {
            "model": self.settings.headroom_model,
            "target_tokens": 900,
            "query": classification.intent.value,
            "instructions": (
                "Keep source identifiers, warnings, negative statements, role restrictions, "
                "version markers, and escalation cues intact."
            ),
            "items": items,
            "user_context": {
                "role": role,
                "risk": classification.risk.value,
            },
        }

        try:
            with httpx.Client(timeout=self.settings.request_timeout_seconds) as client:
                response = client.post(f"{self.settings.headroom_base_url}/v1/compress", json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception:  # noqa: BLE001
            return None

        selected_ids = _extract_selected_ids(data)
        selected = [source_map[source_id] for source_id in selected_ids if source_id in source_map]
        if not selected:
            return None

        token_after = estimate_tokens("\n".join(snippet.content for snippet in selected))
        warnings = []
        negative = []
        escalation_text = None
        if classification.risk.value == "high":
            warnings.append("High-risk context optimization preserved escalation messaging.")
            negative.append("Optimized context does not authorize diagnosis or treatment advice.")
            escalation_text = "Escalate to a qualified clinician or supervisor."
        return OptimizedContext(
            snippets=selected,
            strategy="headroom_cli_proxy",
            headroom_used=True,
            token_count_before=token_before,
            token_count_after=token_after,
            warnings=warnings,
            negative_statements=negative,
            escalation_text=escalation_text,
        )


def _extract_selected_ids(data: dict) -> list[str]:
    candidates = []
    for key in ("selected_ids", "retained_ids", "item_ids"):
        value = data.get(key)
        if isinstance(value, list):
            candidates.extend(item for item in value if isinstance(item, str))
    if candidates:
        return list(dict.fromkeys(candidates))

    items = data.get("items", [])
    selected = []
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict):
                item_id = item.get("id")
                keep = item.get("selected", item.get("keep", True))
                if isinstance(item_id, str) and keep:
                    selected.append(item_id)
    return list(dict.fromkeys(selected))


def deterministic_fallback_optimization(
    snippets: list[SourceSnippet],
    classification: ClassificationResult,
) -> OptimizedContext:
    scored = sorted(
        snippets,
        key=lambda snippet: (
            snippet.title.lower().count(classification.intent.value.split("_")[0]),
            len(snippet.content),
        ),
        reverse=True,
    )
    selected = scored[: min(4, len(scored))]
    token_before = estimate_tokens("\n".join(snippet.content for snippet in snippets))
    token_after = estimate_tokens("\n".join(snippet.content for snippet in selected))
    warnings = ["Headroom unavailable; deterministic optimization fallback used."]
    negative = []
    escalation_text = None
    if classification.risk.value == "high":
        warnings.append("High-risk query retained escalation text during fallback optimization.")
        escalation_text = "Escalate to a qualified clinician or hospital authority."
        negative.append("Fallback optimization cannot approve treatment guidance.")
    return OptimizedContext(
        snippets=selected,
        strategy="deterministic_fallback",
        headroom_used=False,
        token_count_before=token_before,
        token_count_after=token_after,
        warnings=warnings,
        negative_statements=negative,
        escalation_text=escalation_text,
    )
