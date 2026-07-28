"""
governance_service/app/core/redaction.py
------------------------------------------
PII / PHI redaction engine.

Identifies and replaces sensitive identifiers BEFORE any text is stored,
forwarded to PostHog, or passed to downstream services.

Uses deterministic regex patterns as primary engine with an optional
Presidio extension when `presidio-analyzer` is installed.

Synthetic test identifiers (e.g. "Patient ID: TEST-12345") trigger
redaction to validate the pipeline — real patient data must never enter.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from governance_service.app.utils.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

@dataclass
class RedactionPattern:
    name: str
    pattern: re.Pattern
    replacement: str
    category: str


_PATTERNS: List[RedactionPattern] = [
    # US Social Security Number
    RedactionPattern(
        "ssn",
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "[REDACTED:SSN]",
        "national_id",
    ),
    # Date of Birth (various formats)
    RedactionPattern(
        "dob",
        re.compile(
            r"\b(?:dob|date[\s_-]?of[\s_-]?birth)[:\s]+\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b",
            re.IGNORECASE,
        ),
        "[REDACTED:DOB]",
        "dob",
    ),
    # Medical Record Number
    RedactionPattern(
        "mrn",
        re.compile(r"\b(?:MRN|Medical\s+Record\s+(?:No|Number|#))[:\s]*[A-Z0-9\-]{4,20}\b", re.IGNORECASE),
        "[REDACTED:MRN]",
        "patient_id",
    ),
    # Patient ID label
    RedactionPattern(
        "patient_id",
        re.compile(r"\b(?:patient[\s_-]?(?:id|identifier|#|no|number))[:\s]*[A-Z0-9\-]{3,20}\b", re.IGNORECASE),
        "[REDACTED:PATIENT_ID]",
        "patient_id",
    ),
    # NHS number (UK)
    RedactionPattern(
        "nhs_number",
        re.compile(r"\bNHS[\s#:]*\d{3}[\s\-]\d{3}[\s\-]\d{4}\b", re.IGNORECASE),
        "[REDACTED:NHS_NUMBER]",
        "national_id",
    ),
    # Phone numbers
    RedactionPattern(
        "phone",
        re.compile(r"\b(?:\+?1[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b"),
        "[REDACTED:PHONE]",
        "contact",
    ),
    # Email addresses
    RedactionPattern(
        "email",
        re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"),
        "[REDACTED:EMAIL]",
        "contact",
    ),
    # IP addresses
    RedactionPattern(
        "ip_address",
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "[REDACTED:IP]",
        "network",
    ),
    # Named-person indicator (e.g. "Patient John Smith", "for patient Sarah O'Brien")
    RedactionPattern(
        "named_patient",
        re.compile(
            r"\bpatient\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}\b",
            re.IGNORECASE,
        ),
        "[REDACTED:PATIENT_NAME]",
        "patient_name",
    ),
    # Fabricated test IDs used in pipeline validation (TEST-xxxxx)
    RedactionPattern(
        "test_id",
        re.compile(r"\bTEST[-_][A-Z0-9]{3,12}\b", re.IGNORECASE),
        "[REDACTED:TEST_ID]",
        "test_identifier",
    ),
]


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class RedactionResult:
    redacted_text: str
    items_redacted: int
    categories: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def redact(text: str) -> RedactionResult:
    """
    Apply all redaction patterns sequentially.
    Returns a RedactionResult with the sanitised text and metadata.
    """
    result_text = text
    categories: List[str] = []
    findings: List[str] = []
    total_replacements = 0

    for pattern in _PATTERNS:
        matches = pattern.pattern.findall(result_text)
        if matches:
            count = len(matches)
            result_text = pattern.pattern.sub(pattern.replacement, result_text)
            total_replacements += count
            categories.append(pattern.category)
            findings.append(f"{pattern.name}: {count} match(es)")
            log.debug(
                "Redaction applied",
                extra={
                    "pattern": pattern.name,
                    "category": pattern.category,
                    "count": count,
                },
            )

    # Deduplicate categories
    categories = list(dict.fromkeys(categories))

    return RedactionResult(
        redacted_text=result_text,
        items_redacted=total_replacements,
        categories=categories,
        findings=findings,
    )


def needs_redaction(text: str) -> bool:
    """Quick check — returns True if ANY pattern matches."""
    return any(p.pattern.search(text) for p in _PATTERNS)
