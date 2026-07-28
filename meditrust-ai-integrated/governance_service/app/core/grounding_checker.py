"""
governance_service/app/core/grounding_checker.py
--------------------------------------------------
Checks that LLM-generated answers are grounded in the retrieved evidence.

Strategy (deterministic-first):
  1. Extract key noun phrases from the answer.
  2. Check each phrase appears in at least one retrieved chunk.
  3. Penalise absolute statements ("always", "never", "guaranteed") not
     supported by evidence text.
  4. Detect hallucination markers ("as of my knowledge", "I believe").
  5. Calculate a grounding score in [0.0, 1.0].

Optional Gemini verifier:
  When GEMINI_GUARDRAIL_ENABLED=true and a Gemini client is available,
  a constrained verification prompt is sent and the result merged with
  the deterministic score.  This is the ONLY place in governance_service
  that may call Gemini — and only for verification, never for generation.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import List, Optional

from governance_service.app.config import settings
from governance_service.app.utils.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Hallucination markers
# ---------------------------------------------------------------------------

_HALLUCINATION_MARKERS = [
    re.compile(r"\bas\s+of\s+my\s+(knowledge|training|cutoff)\b", re.IGNORECASE),
    re.compile(r"\bI\s+(believe|think|assume)\s+that\b", re.IGNORECASE),
    re.compile(r"\bI\s+am\s+not\s+(entirely\s+)?sure\b", re.IGNORECASE),
    re.compile(r"\bto\s+the\s+best\s+of\s+my\s+(knowledge|understanding)\b", re.IGNORECASE),
    re.compile(r"\bI\s+cannot\s+verify\b", re.IGNORECASE),
    re.compile(r"\bmy\s+training\s+data\b", re.IGNORECASE),
]

_ABSOLUTE_CLAIM_RE = re.compile(
    r"\b(always|never|guaranteed|definitively|without\s+exception|100%|certainly)\b",
    re.IGNORECASE,
)

# Simple noun-phrase extractor (captures NPs of 2–4 words)
_NP_RE = re.compile(r"\b(?:[A-Z][a-z]+\s+){1,3}[A-Z][a-z]+\b|\b\w{5,}\b")


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class GroundingCheckResult:
    score: float
    passed: bool
    unsupported_claims: List[str] = field(default_factory=list)
    hallucination_flags: List[str] = field(default_factory=list)
    method: str = "deterministic"
    latency_ms: int = 0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_grounding(
    answer: str,
    retrieved_chunks: List[str],
    threshold: Optional[float] = None,
) -> GroundingCheckResult:
    """
    Check whether `answer` is grounded in `retrieved_chunks`.

    Parameters
    ----------
    answer:        The LLM-generated answer text.
    retrieved_chunks:
                   Raw text of the chunks retrieved from Chroma.
                   Member 1 / Member 2 should include these in the request.
    threshold:     Override the GROUNDING_PASS_THRESHOLD config value.
    """
    start = time.perf_counter()
    pass_threshold = threshold or settings.GROUNDING_PASS_THRESHOLD

    if not retrieved_chunks:
        # No evidence available — cannot ground anything
        log.warning("Grounding check: no retrieved chunks provided.")
        return GroundingCheckResult(
            score=0.0,
            passed=False,
            unsupported_claims=["No retrieved evidence available for grounding."],
            method="deterministic",
            latency_ms=0,
        )

    corpus = " ".join(retrieved_chunks).lower()

    # ── 1. Hallucination marker check ────────────────────────────────────────
    hallucination_flags: List[str] = []
    for pattern in _HALLUCINATION_MARKERS:
        match = pattern.search(answer)
        if match:
            hallucination_flags.append(match.group())

    # ── 2. Absolute claims not backed by evidence ─────────────────────────────
    unsupported: List[str] = []
    for match in _ABSOLUTE_CLAIM_RE.finditer(answer):
        claim_word = match.group()
        # Check if the surrounding sentence appears in corpus
        sentence = _extract_sentence(answer, match.start())
        sentence_lower = sentence.lower()
        # Simple coverage: are key words from the sentence in the corpus?
        words = [w for w in re.findall(r"\b\w{4,}\b", sentence_lower) if w not in _STOPWORDS]
        if words:
            coverage = sum(1 for w in words if w in corpus) / len(words)
            if coverage < 0.4:
                unsupported.append(f"Absolute claim '{claim_word}' not well-supported: …{sentence[:80]}…")

    # ── 3. Key-phrase coverage ────────────────────────────────────────────────
    key_phrases = list({
        m.group().strip().lower()
        for m in _NP_RE.finditer(answer)
        if len(m.group().strip()) > 4
    })

    if key_phrases:
        covered = sum(1 for kp in key_phrases if kp in corpus)
        coverage_score = covered / len(key_phrases)
    else:
        coverage_score = 1.0   # Nothing to check

    # ── 4. Penalty for hallucination markers ──────────────────────────────────
    penalty = len(hallucination_flags) * 0.10
    raw_score = max(0.0, coverage_score - penalty)
    # Further penalise for unsupported absolute claims
    raw_score = max(0.0, raw_score - len(unsupported) * 0.05)
    score = round(min(1.0, raw_score), 4)

    passed = score >= pass_threshold

    latency = int((time.perf_counter() - start) * 1000)

    log.info(
        "Grounding check complete",
        extra={
            "score": score,
            "passed": passed,
            "unsupported_claims": len(unsupported),
            "hallucination_flags": len(hallucination_flags),
            "method": "deterministic",
        },
    )

    result = GroundingCheckResult(
        score=score,
        passed=passed,
        unsupported_claims=unsupported,
        hallucination_flags=hallucination_flags,
        method="deterministic",
        latency_ms=latency,
    )

    # ── 5. Optional Gemini verifier ───────────────────────────────────────────
    if settings.GEMINI_GUARDRAIL_ENABLED and settings.GEMINI_API_KEY:
        result = _gemini_verify(answer, retrieved_chunks, result)

    return result


def _gemini_verify(
    answer: str,
    chunks: List[str],
    deterministic_result: GroundingCheckResult,
) -> GroundingCheckResult:
    """
    Optional: use Gemini as a second-pass grounding verifier.
    Merges the Gemini score with the deterministic score (average).
    Falls back to deterministic result if Gemini call fails.
    """
    try:
        import google.generativeai as genai  # type: ignore

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        context = "\n\n".join(chunks[:3])   # Limit to 3 chunks for cost control
        prompt = (
            "You are a grounding verification assistant. "
            "Score how well the ANSWER is supported by the CONTEXT on a scale of 0.0 to 1.0. "
            "Return ONLY a JSON object: {\"score\": <float>, \"unsupported\": [<list of short unsupported claim strings>]}\n\n"
            f"CONTEXT:\n{context[:3000]}\n\nANSWER:\n{answer[:1000]}"
        )

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=256,
            ),
        )
        import json
        raw = response.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"```[a-z]*\n?", "", raw).strip("`").strip()
        data = json.loads(raw)

        gemini_score = float(data.get("score", deterministic_result.score))
        gemini_unsupported = data.get("unsupported", [])

        merged_score = round((deterministic_result.score + gemini_score) / 2, 4)
        merged_unsupported = list(set(deterministic_result.unsupported_claims + gemini_unsupported))

        log.info("Gemini grounding verifier used", extra={"gemini_score": gemini_score, "merged": merged_score})

        return GroundingCheckResult(
            score=merged_score,
            passed=merged_score >= settings.GROUNDING_PASS_THRESHOLD,
            unsupported_claims=merged_unsupported,
            hallucination_flags=deterministic_result.hallucination_flags,
            method="gemini_verifier",
            latency_ms=deterministic_result.latency_ms,
        )

    except Exception as exc:
        log.warning("Gemini grounding verifier failed; using deterministic result.", extra={"error": str(exc)})
        return deterministic_result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_sentence(text: str, pos: int) -> str:
    """Extract the sentence containing position `pos` in `text`."""
    start = text.rfind(".", 0, pos)
    end = text.find(".", pos)
    start = 0 if start == -1 else start + 1
    end = len(text) if end == -1 else end + 1
    return text[start:end].strip()


_STOPWORDS = {
    "that", "this", "with", "from", "have", "been", "will", "they",
    "their", "there", "which", "about", "when", "where", "what", "into",
    "more", "also", "such", "each", "other", "than", "then", "some",
}
