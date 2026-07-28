"""
governance_service/app/core/output_guard.py
---------------------------------------------
Orchestrates all output-side validation:

  1. Schema validation (Pydantic)
  2. Safety content check (no clinical directives without disclaimers)
  3. Citation validation (hallucination, status, role, synthetic-as-clinical)
  4. Grounding check (deterministic NLP ± Gemini verifier)
  5. Decision engine → pass / pass_with_warning / regenerate / escalate / block

Decision matrix:
  ┌─────────────────────────────────┬────────────────────────────┐
  │ Condition                       │ Decision                   │
  ├─────────────────────────────────┼────────────────────────────┤
  │ All checks pass                 │ pass                       │
  │ Minor warnings only             │ pass_with_warning          │
  │ Repairable (retry_count == 0)   │ regenerate                 │
  │ Not repairable / retry_count≥1  │ escalate                   │
  │ Injection / emergency / block   │ block                      │
  └─────────────────────────────────┴────────────────────────────┘
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from governance_service.app.config import settings
from governance_service.app.core.citation_validator import (
    CitationValidationResult,
    validate_citations,
)
from governance_service.app.core.grounding_checker import (
    GroundingCheckResult,
    check_grounding,
)
from governance_service.app.utils.logger import get_logger

log = get_logger(__name__)

# Safe message returned when answer is withheld
SAFE_WITHHELD_MSG = (
    "This response has been withheld because it could not be validated "
    "against the available evidence. Please consult a qualified healthcare professional."
)

# Caution always appended to healthcare answers
STANDARD_CAUTION = (
    "This information is sourced from public healthcare guidance and is not a "
    "substitute for professional clinical judgment."
)

# Pattern to catch direct clinical advice slipping through
_CLINICAL_ADVICE_RE = re.compile(
    r"\b(you\s+should\s+(?:take|prescribe|administer|use)\s+\w+|"
    r"the\s+correct\s+treatment\s+is|take\s+\d+\s*mg)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class OutputGuardResult:
    decision: str                      # ValidationStatus values
    answer: Optional[str]
    cautions: List[str] = field(default_factory=list)
    citation_result: Optional[CitationValidationResult] = None
    grounding_result: Optional[GroundingCheckResult] = None
    schema_valid: bool = True
    safety_passed: bool = True
    failure_reasons: List[str] = field(default_factory=list)
    requires_human_review: bool = False
    guard_latency_ms: int = 0
    guardrail_mode: str = "deterministic"


# ---------------------------------------------------------------------------
# Main guard function
# ---------------------------------------------------------------------------

def run_output_guard(
    answer: str,
    citations: List[dict],
    cautions: List[str],
    risk_level: str,
    user_role: str,
    retrieved_document_ids: Optional[List[str]] = None,
    retrieved_chunks: Optional[List[str]] = None,
    retry_count: int = 0,
) -> OutputGuardResult:
    """
    Run all output-side validation and return a routing decision.

    Called by:
      - Member 2 (Orchestration) validate_response node
    """
    start = time.perf_counter()
    failures: List[str] = []
    extra_cautions = list(cautions)
    schema_valid = True
    safety_passed = True

    retrieved_ids: Set[str] = set(retrieved_document_ids or [])
    chunks: List[str] = retrieved_chunks or []

    # ── 1. Basic schema checks ────────────────────────────────────────────────
    if not answer or not answer.strip():
        failures.append("Answer is empty.")
        schema_valid = False

    if len(answer) > 8192:
        failures.append("Answer exceeds maximum length (8192 chars).")
        schema_valid = False

    if not citations:
        failures.append("Answer has no citations — unsupported answer.")
        schema_valid = False

    # ── 2. Safety content check ───────────────────────────────────────────────
    if _CLINICAL_ADVICE_RE.search(answer):
        failures.append("Answer contains direct clinical advice which is outside the permitted scope.")
        safety_passed = False
        extra_cautions.append(
            "This response has been flagged for containing language that may suggest clinical advice. "
            "It must be reviewed by a qualified professional."
        )

    # Ensure standard caution is always present
    if STANDARD_CAUTION not in extra_cautions:
        extra_cautions.append(STANDARD_CAUTION)

    # ── 3. Citation validation ────────────────────────────────────────────────
    citation_result: Optional[CitationValidationResult] = None
    if citations:
        citation_result = validate_citations(
            citations=citations,
            retrieved_document_ids=retrieved_ids,
            user_role=user_role,
            answer_text=answer,
        )
        if not citation_result.all_passed:
            for check in citation_result.checks:
                if not check.passed:
                    failures.append(f"Citation '{check.document_id}': {check.failure_reason}")
            if citation_result.unauthorised_sources:
                safety_passed = False
                failures.append(f"Unauthorised sources in citations: {citation_result.unauthorised_sources}")

    # ── 4. Grounding check ────────────────────────────────────────────────────
    grounding_result: Optional[GroundingCheckResult] = None
    if chunks and answer.strip():
        grounding_result = check_grounding(
            answer=answer,
            retrieved_chunks=chunks,
        )
        if not grounding_result.passed:
            failures.append(
                f"Grounding score {grounding_result.score:.2f} below threshold "
                f"{settings.GROUNDING_PASS_THRESHOLD}."
            )
            if grounding_result.unsupported_claims:
                extra_cautions.append(
                    f"Note: {len(grounding_result.unsupported_claims)} claim(s) in this answer "
                    "could not be fully verified against retrieved evidence."
                )

    # ── 5. Decision engine ────────────────────────────────────────────────────
    decision, final_answer, requires_human = _decide(
        failures=failures,
        safety_passed=safety_passed,
        schema_valid=schema_valid,
        answer=answer,
        retry_count=retry_count,
        risk_level=risk_level,
    )

    latency = int((time.perf_counter() - start) * 1000)

    log.info(
        "Output guard decision",
        extra={
            "decision": decision,
            "failures": len(failures),
            "schema_valid": schema_valid,
            "safety_passed": safety_passed,
            "latency_ms": latency,
        },
    )

    return OutputGuardResult(
        decision=decision,
        answer=final_answer,
        cautions=list(dict.fromkeys(extra_cautions)),   # deduplicate, preserve order
        citation_result=citation_result,
        grounding_result=grounding_result,
        schema_valid=schema_valid,
        safety_passed=safety_passed,
        failure_reasons=failures,
        requires_human_review=requires_human,
        guard_latency_ms=latency,
        guardrail_mode="deterministic",
    )


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------

def _decide(
    failures: List[str],
    safety_passed: bool,
    schema_valid: bool,
    answer: str,
    retry_count: int,
    risk_level: str,
) -> tuple[str, Optional[str], bool]:
    """
    Returns (decision, answer_to_return, requires_human_review).
    """
    # Hard block conditions
    if not safety_passed:
        return "block", SAFE_WITHHELD_MSG, True

    if not schema_valid:
        if retry_count == 0:
            return "regenerate", None, False
        return "escalate", SAFE_WITHHELD_MSG, True

    # No failures at all
    if not failures:
        return "pass", answer, False

    # Citation or grounding failures — repairable
    repairable_failures = [f for f in failures if "Citation" in f or "Grounding" in f or "grounding" in f]
    critical_failures = [f for f in failures if f not in repairable_failures]

    if critical_failures:
        if retry_count == 0:
            return "regenerate", None, False
        return "escalate", SAFE_WITHHELD_MSG, True

    if repairable_failures:
        if retry_count == 0 and len(repairable_failures) > 2:
            return "regenerate", None, False
        # Minor citation warnings — pass with warning
        return "pass_with_warning", answer, False

    return "pass_with_warning", answer, False
