from __future__ import annotations

from orchestration_service.app.models import (
    ClassificationReason,
    ClassificationResult,
    IntentType,
    RiskLevel,
)


INTENT_RULES: list[tuple[IntentType, tuple[str, ...], float]] = [
    (IntentType.emergency, ("chest pain", "not breathing", "seizure", "stroke", "collapse"), 0.98),
    (IntentType.diagnosis_or_treatment, ("diagnose", "treatment plan", "should i take", "prescribe"), 0.88),
    (IntentType.medication_question, ("dosage", "dose", "medication", "drug interaction"), 0.83),
    (IntentType.hospital_process, ("discharge", "triage", "admission", "referral", "workflow", "sop"), 0.80),
]

RISK_RULES: list[tuple[RiskLevel, tuple[str, ...], float]] = [
    (RiskLevel.high, ("emergency", "urgent", "pregnant", "child", "overdose", "suicidal"), 0.95),
    (RiskLevel.high, ("diagnose", "prescribe", "treatment plan", "drug interaction"), 0.90),
    (RiskLevel.medium, ("dosage", "medication", "symptom", "side effect"), 0.72),
]


def classify_deterministically(query: str, ambiguous_threshold: float) -> ClassificationResult:
    lowered = query.lower()
    reasons: list[ClassificationReason] = []

    intent = IntentType.general_info
    intent_score = 0.40
    for label, keywords, score in INTENT_RULES:
        if any(keyword in lowered for keyword in keywords):
            intent = label
            intent_score = score
            reasons.append(ClassificationReason(label=label.value, score=score, rule="keyword_intent"))
            break

    risk = RiskLevel.low
    risk_score = 0.25
    for label, keywords, score in RISK_RULES:
        if any(keyword in lowered for keyword in keywords):
            risk = label
            risk_score = score
            reasons.append(ClassificationReason(label=label.value, score=score, rule="keyword_risk"))
            break

    if len(query.split()) < 4 or "?" not in query:
        reasons.append(ClassificationReason(label="ambiguous_form", score=0.58, rule="short_or_implicit_query"))
        intent_score = max(intent_score, 0.58)

    ambiguous = intent_score <= ambiguous_threshold or risk_score <= ambiguous_threshold
    if intent == IntentType.general_info and ambiguous:
        intent = IntentType.unknown

    return ClassificationResult(
        intent=intent,
        risk=risk,
        ambiguous=ambiguous,
        used_gemini=False,
        reasons=reasons,
    )
