"""
governance_service/app/core/risk_classifier.py
------------------------------------------------
Deterministic intent and risk classification for healthcare queries.

Classification is FULLY DETERMINISTIC — no LLM calls.
This ensures the guardrail never fails due to model unavailability.

Risk levels map directly to LangGraph routing:
  LOW / MEDIUM  → proceed through normal RAG pipeline
  HIGH          → route to human_escalation node
  CRITICAL      → immediate block, no further processing
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

from governance_service.app.utils.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Intent categories
# ---------------------------------------------------------------------------

class IntentCategory(str, Enum):
    KNOWLEDGE_SEARCH       = "knowledge_search"        # ✅ Supported
    POLICY_LOOKUP          = "policy_lookup"           # ✅ Supported
    PROCESS_GUIDANCE       = "process_guidance"        # ✅ Supported
    CLARIFICATION          = "clarification"           # ✅ Supported (low confidence)
    DIAGNOSIS_REQUEST      = "diagnosis_request"       # 🚫 Escalate
    PRESCRIPTION_REQUEST   = "prescription_request"   # 🚫 Escalate
    DOSAGE_REQUEST         = "dosage_request"          # 🚫 Escalate
    TREATMENT_SELECTION    = "treatment_selection"     # 🚫 Escalate
    EMERGENCY_REQUEST      = "emergency_request"       # 🚫 Escalate + Block
    PATIENT_SPECIFIC       = "patient_specific"        # 🚫 Escalate
    PROMPT_INJECTION       = "prompt_injection"        # 🚫 Block immediately
    UNAUTHORIZED           = "unauthorized"            # 🚫 Block
    UNKNOWN                = "unknown"


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

@dataclass
class RulePattern:
    intent: IntentCategory
    patterns: List[re.Pattern]
    risk_level: str
    reason: str


_RULES: List[RulePattern] = [
    # ── CRITICAL: Prompt injection ─────────────────────────────────────────────
    RulePattern(
        IntentCategory.PROMPT_INJECTION,
        [
            re.compile(r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)", re.IGNORECASE),
            re.compile(r"disregard\s+(your\s+)?(system\s+)?(prompt|instructions?)", re.IGNORECASE),
            re.compile(r"you\s+are\s+now\s+(a|an|the)\s+(?!healthcare|medical\s+knowledge)", re.IGNORECASE),
            re.compile(r"pretend\s+(you\s+are|to\s+be)\s+(?!a\s+healthcare)", re.IGNORECASE),
            re.compile(r"jailbreak|DAN\s+mode|developer\s+mode|unrestricted\s+mode", re.IGNORECASE),
            re.compile(r"<\s*script[^>]*>", re.IGNORECASE),
            re.compile(r"system\s*:\s*you\s+must", re.IGNORECASE),
            re.compile(r"override\s+(safety|guardrail|filter|restriction)", re.IGNORECASE),
            re.compile(r"bypass\s+(the\s+)?(safety|filter|restriction|guard)", re.IGNORECASE),
        ],
        "critical",
        "Prompt injection attempt detected.",
    ),

    # ── CRITICAL: Emergency ───────────────────────────────────────────────────
    RulePattern(
        IntentCategory.EMERGENCY_REQUEST,
        [
            re.compile(r"\b(call\s+911|cardiac\s+arrest|code\s+blue|active\s+bleed(ing)?|stroke\s+in\s+progress)\b", re.IGNORECASE),
            re.compile(r"\bpatient\s+is\s+(currently\s+)?(dying|unconscious|unresponsive|coding)", re.IGNORECASE),
            re.compile(r"\b(currently\s+coding|patient\s+coding|is\s+coding)\b", re.IGNORECASE),
            re.compile(r"\bemergency\s+(room|department|treatment)\s+right\s+now\b", re.IGNORECASE),
        ],
        "critical",
        "Emergency scenario detected. Immediate human escalation required.",
    ),

    # ── HIGH: Diagnosis ───────────────────────────────────────────────────────
    RulePattern(
        IntentCategory.DIAGNOSIS_REQUEST,
        [
            re.compile(r"\b(diagnose|diagnosis|what\s+disease|what\s+condition|do\s+I\s+have|does\s+(?:the\s+)?patient\s+have)\b", re.IGNORECASE),
            re.compile(r"\b(is\s+it\s+(?:cancer|diabetes|covid|pneumonia|sepsis)|could\s+this\s+be\s+\w+\s+disease)\b", re.IGNORECASE),
            re.compile(r"\bwhat\s+is\s+wrong\s+with\s+(me|the\s+patient|him|her)\b", re.IGNORECASE),
        ],
        "high",
        "Query requests a clinical diagnosis. Human escalation required.",
    ),

    # ── HIGH: Prescription ────────────────────────────────────────────────────
    RulePattern(
        IntentCategory.PRESCRIPTION_REQUEST,
        [
            re.compile(r"\b(prescribe|prescription|should\s+(?:I|we)\s+prescribe|write\s+a\s+prescription)\b", re.IGNORECASE),
            re.compile(r"\b(recommend\s+(?:a\s+)?medication\s+for|which\s+drug\s+should\s+I\s+give)\b", re.IGNORECASE),
        ],
        "high",
        "Query requests prescribing advice. Human escalation required.",
    ),

    # ── HIGH: Dosage ──────────────────────────────────────────────────────────
    RulePattern(
        IntentCategory.DOSAGE_REQUEST,
        [
            re.compile(r"\b(dosage|dose|how\s+much\s+(?:to\s+)?(?:give|administer|prescribe)|mg\s+per\s+kg)\b", re.IGNORECASE),
            re.compile(r"\b(calculate\s+(?:the\s+)?dose|maximum\s+(?:safe\s+)?dose)\b", re.IGNORECASE),
            re.compile(r"\b(\d+\s*mg|\d+\s*mcg|\d+\s*units?)\s+(?:of\s+)?\w+\s+(?:for|to)\s+(?:this\s+)?patient\b", re.IGNORECASE),
        ],
        "high",
        "Query requests dosage calculation. Human escalation required.",
    ),

    # ── HIGH: Treatment selection ─────────────────────────────────────────────
    RulePattern(
        IntentCategory.TREATMENT_SELECTION,
        [
            re.compile(r"\b(which\s+treatment|best\s+treatment|treat\s+(?:this\s+)?patient\s+with|treatment\s+plan\s+for)\b", re.IGNORECASE),
            re.compile(r"\b(should\s+(?:I|we)\s+(?:use|choose|start)\s+(?:treatment|therapy|medication))\b", re.IGNORECASE),
        ],
        "high",
        "Query requests treatment selection. Human escalation required.",
    ),

    # ── HIGH: Patient-specific ────────────────────────────────────────────────
    RulePattern(
        IntentCategory.PATIENT_SPECIFIC,
        [
            re.compile(r"\b(for\s+my\s+patient|patient\s+(?:John|Jane|Sarah|David|Mary|James)\b)", re.IGNORECASE),
            re.compile(r"\b(this\s+specific\s+patient|patient\s+in\s+(?:room|bed|ward)\s+\d+)\b", re.IGNORECASE),
            re.compile(r"\bMRN[:\s]*[A-Z0-9\-]+\b", re.IGNORECASE),
        ],
        "high",
        "Query references a specific patient. Human escalation required.",
    ),
]

# ── LOW confidence: Knowledge support ────────────────────────────────────────
_KNOWLEDGE_PATTERNS: List[re.Pattern] = [
    re.compile(r"\b(guideline|guidance|protocol|standard|recommendation|policy|procedure|SOP)\b", re.IGNORECASE),
    re.compile(r"\b(infection\s+control|hand\s+hygiene|PPE|isolation|sterilization)\b", re.IGNORECASE),
    re.compile(r"\b(CDC|WHO|evidence|best\s+practice|clinical\s+standard)\b", re.IGNORECASE),
    re.compile(r"\b(what\s+is\s+the\s+procedure|how\s+should\s+(?:staff|nurses?|clinicians?)\s+handle)\b", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class ClassificationResult:
    intent: IntentCategory
    risk_level: str       # "low" | "medium" | "high" | "critical"
    reason: str
    matched_rules: List[str] = field(default_factory=list)
    requires_escalation: bool = False
    requires_block: bool = False
    confidence: float = 1.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify(query: str) -> ClassificationResult:
    """
    Classify the intent and risk level of a query.
    Returns a ClassificationResult with routing guidance.
    """
    matched: List[RulePattern] = []

    for rule in _RULES:
        for pattern in rule.patterns:
            if pattern.search(query):
                matched.append(rule)
                break  # one match per rule is enough

    if not matched:
        # Check if it looks like a knowledge query
        knowledge_signals = sum(
            1 for p in _KNOWLEDGE_PATTERNS if p.search(query)
        )
        if knowledge_signals >= 1:
            return ClassificationResult(
                intent=IntentCategory.KNOWLEDGE_SEARCH,
                risk_level="low",
                reason="Knowledge/guidance search detected.",
                confidence=min(0.5 + knowledge_signals * 0.15, 1.0),
            )
        return ClassificationResult(
            intent=IntentCategory.UNKNOWN,
            risk_level="medium",
            reason="Intent could not be confidently classified; routing to standard RAG with caution.",
            confidence=0.4,
        )

    # Pick highest-severity match
    risk_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    matched.sort(key=lambda r: risk_order.get(r.risk_level, 0), reverse=True)
    top = matched[0]

    return ClassificationResult(
        intent=top.intent,
        risk_level=top.risk_level,
        reason=top.reason,
        matched_rules=[r.intent.value for r in matched],
        requires_escalation=top.risk_level in ("high", "critical"),
        requires_block=top.intent in (
            IntentCategory.PROMPT_INJECTION,
            IntentCategory.EMERGENCY_REQUEST,
        ),
        confidence=1.0,
    )
