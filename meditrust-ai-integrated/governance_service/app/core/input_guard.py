"""
governance_service/app/core/input_guard.py
--------------------------------------------
Orchestrates all input-side safety checks in a fixed pipeline:

  1. Length enforcement
  2. PII / PHI redaction
  3. Injection detection
  4. Risk / intent classification
  5. Role-based access check
  6. Conversation-history turn limit

Returns a fully typed InputGuardResult that the API route maps to the
shared InputGuardResponse schema.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from governance_service.app.config import settings
from governance_service.app.core.redaction import redact, RedactionResult
from governance_service.app.core.risk_classifier import classify, ClassificationResult, IntentCategory
from governance_service.app.utils.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Allowed roles for standard knowledge queries
# ---------------------------------------------------------------------------

ALLOWED_ROLES = {
    "doctor", "nurse", "pharmacist", "compliance_officer", "administrator", "anonymous",
}

# Roles that may access synthetic SOPs
SYNTHETIC_ALLOWED_ROLES = {
    "administrator", "compliance_officer", "doctor", "nurse", "pharmacist",
}


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class InjectionFinding:
    pattern_matched: str
    severity: str
    description: str


@dataclass
class InputGuardResult:
    decision: str              # "allow" | "redact" | "warn" | "escalate" | "block"
    risk_level: str            # "low" | "medium" | "high" | "critical"
    risk_reason: str
    safe_query: str            # Sanitised query to use downstream
    redaction: Optional[RedactionResult] = None
    injection_findings: List[InjectionFinding] = field(default_factory=list)
    requires_human_review: bool = False
    guard_latency_ms: int = 0
    guardrail_mode: str = "deterministic"
    failure_reasons: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Main guard function
# ---------------------------------------------------------------------------

def run_input_guard(
    query: str,
    user_role: str = "anonymous",
    conversation_history: Optional[List[Dict]] = None,
) -> InputGuardResult:
    """
    Run all input-side safety checks and return a routing decision.

    Called by:
      - Member 2 (Orchestration) input_guard node
      - Member 4 (Gateway) before forwarding to orchestration
    """
    start = time.perf_counter()
    history = conversation_history or []
    failures: List[str] = []

    # ── 1. Length check ──────────────────────────────────────────────────────
    if len(query) > settings.MAX_QUERY_LENGTH:
        log.warning("Query exceeds maximum length", extra={"length": len(query)})
        return _build(
            "block",
            "low",
            f"Query exceeds the maximum allowed length of {settings.MAX_QUERY_LENGTH} characters.",
            query[:settings.MAX_QUERY_LENGTH],
            start,
        )

    # ── 2. Conversation history depth check ──────────────────────────────────
    if len(history) > settings.MAX_CONVERSATION_TURNS:
        failures.append("Conversation history exceeds turn limit.")
        log.warning("Conversation history too long", extra={"turns": len(history)})

    # ── 3. Redaction ─────────────────────────────────────────────────────────
    redaction_result: Optional[RedactionResult] = None
    working_query = query

    try:
        redaction_result = redact(query)
        if redaction_result.items_redacted > 0:
            working_query = redaction_result.redacted_text
            log.info(
                "Query redacted",
                extra={
                    "items_redacted": redaction_result.items_redacted,
                    "categories": redaction_result.categories,
                },
            )
    except Exception as exc:
        log.error("Redaction failed; proceeding with raw query", extra={"error": str(exc)})
        failures.append("Redaction engine error — proceeding with unredacted query.")

    # ── 4. Risk / intent classification ──────────────────────────────────────
    classification: ClassificationResult = classify(working_query)

    log.info(
        "Intent classified",
        extra={
            "intent": classification.intent.value,
            "risk_level": classification.risk_level,
            "confidence": classification.confidence,
        },
    )

    # ── 5. BLOCK: Injection ───────────────────────────────────────────────────
    if classification.intent == IntentCategory.PROMPT_INJECTION:
        findings = [
            InjectionFinding(
                pattern_matched=rule,
                severity="high",
                description="Prompt injection pattern detected.",
            )
            for rule in classification.matched_rules
        ]
        return _build(
            "block",
            "critical",
            classification.reason,
            "[QUERY BLOCKED — injection attempt]",
            start,
            redaction=redaction_result,
            injection_findings=findings,
        )

    # ── 6. BLOCK/ESCALATE: Emergency ─────────────────────────────────────────
    if classification.intent.value == "emergency_request":
        return _build(
            "block",
            "critical",
            classification.reason,
            working_query,
            start,
            redaction=redaction_result,
            requires_human=True,
        )

    # ── 7. ESCALATE: High-risk clinical intent ────────────────────────────────
    if classification.requires_escalation and settings.HIGH_RISK_ESCALATION_ENABLED:
        return _build(
            "escalate",
            classification.risk_level,
            classification.reason,
            working_query,
            start,
            redaction=redaction_result,
            requires_human=True,
        )

    # ── 8. Role check (medium guard) ─────────────────────────────────────────
    if user_role not in ALLOWED_ROLES:
        return _build(
            "block",
            "medium",
            f"User role '{user_role}' is not authorized.",
            working_query,
            start,
        )

    # ── 9. Allow / warn ───────────────────────────────────────────────────────
    decision = "allow"
    risk_level = classification.risk_level

    has_redaction = redaction_result and redaction_result.items_redacted > 0
    if has_redaction or failures:
        decision = "redact" if has_redaction else "warn"

    return _build(
        decision,
        risk_level,
        classification.reason,
        working_query,
        start,
        redaction=redaction_result,
        failures=failures,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build(
    decision: str,
    risk_level: str,
    reason: str,
    safe_query: str,
    start: float,
    redaction: Optional[RedactionResult] = None,
    injection_findings: Optional[List[InjectionFinding]] = None,
    requires_human: bool = False,
    failures: Optional[List[str]] = None,
) -> InputGuardResult:
    latency = int((time.perf_counter() - start) * 1000)
    return InputGuardResult(
        decision=decision,
        risk_level=risk_level,
        risk_reason=reason,
        safe_query=safe_query,
        redaction=redaction,
        injection_findings=injection_findings or [],
        requires_human_review=requires_human,
        guard_latency_ms=latency,
        guardrail_mode="deterministic",
        failure_reasons=failures or [],
    )
