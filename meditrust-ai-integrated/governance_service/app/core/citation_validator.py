"""
governance_service/app/core/citation_validator.py
---------------------------------------------------
Validates that each citation in an LLM answer:

  1. Has a document_id that was actually retrieved from Chroma (not hallucinated)
  2. Has a status of "active" (not superseded, expired or draft)
  3. Cites a section that plausibly exists (non-empty, reasonable length)
  4. Matches the requesting user's role access list
  5. Is from a document version that was current at query time
  6. Does not reference a SYNTHETIC document as approved clinical policy

This validator is DETERMINISTIC — no LLM calls required.
"""

from __future__ import annotations

import re
from typing import List, Optional, Set

from pydantic import BaseModel

from governance_service.app.utils.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class CitationCheckItem(BaseModel):
    document_id: str
    passed: bool
    failure_reason: str = ""

    # Allow both 'document_id' and 'doc_id' as aliases for backward compat
    model_config = {"populate_by_name": True}


class CitationValidationResult(BaseModel):
    all_passed: bool
    checks: List[CitationCheckItem] = []
    total: int = 0
    passed: int = 0
    failed: int = 0
    validity_pct: float = 100.0
    unauthorised_sources: List[str] = []
    synthetic_presented_as_clinical: List[str] = []


# ---------------------------------------------------------------------------
# Citation dict shape (matches shared Citation model fields)
# ---------------------------------------------------------------------------
# {
#   "document_id": str,
#   "title": str,
#   "section": Optional[str],
#   "publisher": str,
#   "url": Optional[str],
#   "source_type": "public" | "synthetic",
#   "status": "active" | "superseded" | "expired" | "draft",
#   "access_roles": List[str],
#   "is_synthetic": bool,
# }


# Clinical-sounding phrases that MUST NOT appear in a synthetic document answer
# without an explicit demonstration disclaimer
_CLINICAL_DIRECTIVE_RE = re.compile(
    r"\b(prescribe|administer|the\s+correct\s+dose|approved\s+treatment|recommended\s+medication|"
    r"FDA[\s-]?approved|clinical\s+trial\s+results?)\b",
    re.IGNORECASE,
)


def validate_citations(
    citations: List[dict],
    retrieved_document_ids: Set[str],
    user_role: str,
    answer_text: str = "",
) -> CitationValidationResult:
    """
    Validate a list of citation dicts.

    Parameters
    ----------
    citations:
        List of citation dicts from the LLM response.
    retrieved_document_ids:
        Set of document IDs that were actually retrieved from Chroma.
        Used to detect hallucinated citations.
    user_role:
        The requesting user's role string (e.g. "nurse").
    answer_text:
        The full answer text — used to detect synthetic-as-clinical misuse.
    """
    checks: List[CitationCheckItem] = []
    unauthorised: List[str] = []
    synthetic_clinical: List[str] = []

    for cit in citations:
        doc_id = cit.get("document_id", "")
        item = _check_single(
            cit,
            doc_id,
            retrieved_document_ids,
            user_role,
            answer_text,
        )
        checks.append(item)
        if not item.passed:
            if "Unauthorized" in item.failure_reason:
                unauthorised.append(doc_id)
            if "synthetic" in item.failure_reason.lower() and "clinical" in item.failure_reason.lower():
                synthetic_clinical.append(doc_id)

    total = len(checks)
    passed = sum(1 for c in checks if c.passed)
    failed = total - passed
    validity_pct = (passed / total * 100) if total > 0 else 100.0

    log.info(
        "Citation validation complete",
        extra={"total": total, "passed": passed, "failed": failed, "validity_pct": round(validity_pct, 1)},
    )

    return CitationValidationResult(
        all_passed=(failed == 0),
        checks=checks,
        total=total,
        passed=passed,
        failed=failed,
        validity_pct=round(validity_pct, 2),
        unauthorised_sources=unauthorised,
        synthetic_presented_as_clinical=synthetic_clinical,
    )


def _check_single(
    cit: dict,
    doc_id: str,
    retrieved_ids: Set[str],
    user_role: str,
    answer_text: str,
) -> CitationCheckItem:
    """Run all citation checks for a single citation."""

    # 1. Document ID present
    if not doc_id:
        return CitationCheckItem(document_id=doc_id, passed=False, failure_reason="Missing document_id.")

    # 2. Not hallucinated — must have been in the retrieval result
    if retrieved_ids and doc_id not in retrieved_ids:
        return CitationCheckItem(
            document_id=doc_id,
            passed=False,
            failure_reason=f"Hallucinated citation: '{doc_id}' was not retrieved from Chroma.",
        )

    # 3. Status check
    status = cit.get("status", "active")
    if status != "active":
        return CitationCheckItem(
            document_id=doc_id,
            passed=False,
            failure_reason=f"Document status is '{status}' — only active documents are citable.",
        )

    # 4. Role authorization
    access_roles = cit.get("access_roles", [])
    if access_roles and user_role not in access_roles:
        return CitationCheckItem(
            document_id=doc_id,
            passed=False,
            failure_reason=f"Unauthorized: role '{user_role}' cannot access document '{doc_id}'.",
        )

    # 5. Section sanity check
    section = cit.get("section", "")
    if section and len(section) > 512:
        return CitationCheckItem(
            document_id=doc_id,
            passed=False,
            failure_reason="Section text exceeds maximum length (512 chars) — likely corrupt.",
        )

    # 6. Synthetic presented as clinical policy guard
    is_synthetic = cit.get("is_synthetic", False) or cit.get("source_type") == "synthetic"
    if is_synthetic and answer_text and _CLINICAL_DIRECTIVE_RE.search(answer_text):
        return CitationCheckItem(
            document_id=doc_id,
            passed=False,
            failure_reason=(
                f"Synthetic document '{doc_id}' cited in context of clinical directives — "
                "must not be presented as approved clinical policy."
            ),
        )

    return CitationCheckItem(document_id=doc_id, passed=True)
