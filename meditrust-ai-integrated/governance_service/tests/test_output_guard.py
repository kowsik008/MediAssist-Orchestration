"""
governance_service/tests/test_output_guard.py
-----------------------------------------------
Unit tests for the output guard engine.
"""

from __future__ import annotations

import pytest

from governance_service.app.core.output_guard import run_output_guard, SAFE_WITHHELD_MSG

VALID_CITATION = {
    "document_id": "CDC-IPC-001",
    "title": "CDC Standard Precautions",
    "section": "Hand Hygiene",
    "publisher": "CDC",
    "source_type": "public",
    "status": "active",
    "is_synthetic": False,
    "access_roles": [],
    "url": "https://www.cdc.gov",
    "version_date": "2024-01",
    "licence": "Public Domain",
}

VALID_CHUNKS = [
    "Hand hygiene is the single most important measure to reduce healthcare-associated infections. "
    "Healthcare workers should perform hand hygiene before and after patient contact."
]

VALID_ANSWER = (
    "According to CDC Standard Precautions, healthcare workers should perform hand hygiene "
    "before and after patient contact using soap and water or alcohol-based hand rubs."
)


class TestPassDecision:
    def test_valid_answer_passes(self):
        result = run_output_guard(
            answer=VALID_ANSWER,
            citations=[VALID_CITATION],
            cautions=[],
            risk_level="low",
            user_role="nurse",
            retrieved_document_ids=["CDC-IPC-001"],
            retrieved_chunks=VALID_CHUNKS,
        )
        assert result.decision in ("pass", "pass_with_warning")
        assert result.answer is not None
        assert SAFE_WITHHELD_MSG not in (result.answer or "")

    def test_standard_caution_always_appended(self):
        result = run_output_guard(
            answer=VALID_ANSWER,
            citations=[VALID_CITATION],
            cautions=[],
            risk_level="low",
            user_role="nurse",
            retrieved_document_ids=["CDC-IPC-001"],
        )
        assert any("not a substitute" in c.lower() for c in result.cautions)

    def test_latency_recorded(self):
        result = run_output_guard(
            answer=VALID_ANSWER,
            citations=[VALID_CITATION],
            cautions=[],
            risk_level="low",
            user_role="nurse",
            retrieved_document_ids=["CDC-IPC-001"],
        )
        assert result.guard_latency_ms >= 0


class TestCitationFailures:
    def test_hallucinated_citation_fails(self):
        result = run_output_guard(
            answer="According to FAKE-DOC-999, the guideline says X.",
            citations=[{**VALID_CITATION, "document_id": "FAKE-DOC-999"}],
            cautions=[],
            risk_level="low",
            user_role="nurse",
            retrieved_document_ids=["CDC-IPC-001"],  # FAKE-DOC-999 not in this set
        )
        assert result.decision in ("regenerate", "escalate", "pass_with_warning")
        assert result.citation_result is not None
        assert not result.citation_result.all_passed

    def test_superseded_citation_fails(self):
        superseded = {**VALID_CITATION, "status": "superseded"}
        result = run_output_guard(
            answer=VALID_ANSWER,
            citations=[superseded],
            cautions=[],
            risk_level="low",
            user_role="nurse",
            retrieved_document_ids=["CDC-IPC-001"],
        )
        assert result.citation_result is not None
        assert not result.citation_result.all_passed

    def test_no_citations_fails_schema(self):
        result = run_output_guard(
            answer=VALID_ANSWER,
            citations=[],
            cautions=[],
            risk_level="low",
            user_role="nurse",
        )
        assert result.decision in ("regenerate", "escalate", "block")
        assert not result.schema_valid

    def test_unauthorized_role_fails(self):
        restricted = {**VALID_CITATION, "access_roles": ["doctor", "pharmacist"]}
        result = run_output_guard(
            answer=VALID_ANSWER,
            citations=[restricted],
            cautions=[],
            risk_level="low",
            user_role="anonymous",
            retrieved_document_ids=["CDC-IPC-001"],
        )
        assert result.citation_result is not None
        assert any(not c.passed for c in result.citation_result.checks)


class TestSafetyChecks:
    def test_clinical_advice_blocked(self):
        result = run_output_guard(
            answer="You should take 500mg of amoxicillin twice daily.",
            citations=[VALID_CITATION],
            cautions=[],
            risk_level="low",
            user_role="nurse",
            retrieved_document_ids=["CDC-IPC-001"],
        )
        assert result.decision == "block"
        assert not result.safety_passed
        assert result.answer == SAFE_WITHHELD_MSG

    def test_synthetic_as_clinical_fails(self):
        synthetic_citation = {
            **VALID_CITATION,
            "document_id": "SYN-SOP-001",
            "is_synthetic": True,
            "source_type": "synthetic",
        }
        # Use an answer with a phrase matching _CLINICAL_DIRECTIVE_RE ("approved treatment")
        clinical_answer = "The approved treatment for this condition is documented in SYN-SOP-001."
        result = run_output_guard(
            answer=clinical_answer,
            citations=[synthetic_citation],
            cautions=[],
            risk_level="low",
            user_role="nurse",
            retrieved_document_ids=["SYN-SOP-001"],
        )
        assert result.citation_result is not None
        assert len(result.citation_result.synthetic_presented_as_clinical) >= 1

    def test_empty_answer_fails(self):
        result = run_output_guard(
            answer="",
            citations=[VALID_CITATION],
            cautions=[],
            risk_level="low",
            user_role="nurse",
            retrieved_document_ids=["CDC-IPC-001"],
        )
        assert not result.schema_valid


class TestRetryBehavior:
    def test_repairable_failure_triggers_regenerate_on_first_try(self):
        result = run_output_guard(
            answer="According to FAKE-999, the guideline says something.",
            citations=[{**VALID_CITATION, "document_id": "FAKE-999"}],
            cautions=[],
            risk_level="low",
            user_role="nurse",
            retrieved_document_ids=["CDC-IPC-001"],
            retry_count=0,
        )
        # First retry → regenerate or pass_with_warning
        assert result.decision in ("regenerate", "pass_with_warning")

    def test_repeated_failure_escalates(self):
        result = run_output_guard(
            answer="",   # Empty answer will fail schema
            citations=[VALID_CITATION],
            cautions=[],
            risk_level="low",
            user_role="nurse",
            retrieved_document_ids=["CDC-IPC-001"],
            retry_count=1,  # Already retried once → escalate
        )
        assert result.decision in ("escalate", "block")
