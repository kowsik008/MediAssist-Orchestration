# MediTrust AI — Governance Service
**Member 3 | Port 8002 | Python FastAPI**

> Responsible-use boundary: This service enforces guardrails but does **not** replace qualified clinical judgment.

---

## Overview

The Governance Service is the safety and observability backbone of MediTrust AI. It provides:

| Capability | Implementation |
|---|---|
| Input guardrails | PII redaction → injection detection → risk classification → role check |
| Output guardrails | Schema validation → citation check → grounding check → decision engine |
| Analytics cascade | PostHog → SQLite → JSONL (zero event loss) |
| Audit trail | SHA-256 query hashes, never raw text |
| KPI dashboard data | Aggregated from SQLite, exported as JSON or CSV |
| Feedback collection | Hashed comments, 1–5 star ratings |

---

## Quick Start

```powershell
# From the repository root (meditrust-ai/)
.\scripts\start_governance.ps1
```

Or manually:

```powershell
# 1. Create virtual environment
cd governance_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up config
copy .env.example .env
# Edit .env — add PostHog token if available (optional)

# 4. Create storage directories
New-Item -ItemType Directory -Force -Path ..\storage\audit
New-Item -ItemType Directory -Force -Path ..\storage\analytics

# 5. Start service
$env:PYTHONPATH = ".."
python -m uvicorn governance_service.app.main:app --host 127.0.0.1 --port 8002 --reload
```

Service endpoints:
- **API Docs**: http://127.0.0.1:8002/docs
- **Health**: http://127.0.0.1:8002/api/v1/health
- **OpenAPI JSON**: http://127.0.0.1:8002/openapi.json

---

## API Reference

### Input Guard
```
POST /api/v1/guard/input
```
Screen a query before retrieval. Returns `GuardDecision` and sanitised `safe_query`.

**Decision values:**
| Decision | Meaning | Next step |
|---|---|---|
| `allow` | Safe to proceed | Continue to cache/RAG |
| `redact` | PII found and removed | Use `safe_query` field |
| `warn` | Minor concern | Proceed with caution |
| `escalate` | High-risk clinical intent | Route to `human_escalation` node |
| `block` | Injection / emergency / unauthorised | Stop, return safe message |

### Output Guard
```
POST /api/v1/guard/output
```
Validate LLM answer. Returns `ValidationStatus` and optionally strips the answer.

**Decision values:**
| Decision | Meaning | Next step |
|---|---|---|
| `pass` | All checks passed | Cache and return |
| `pass_with_warning` | Minor issues | Return with caution banner |
| `regenerate` | Repairable (first attempt) | One controlled retry |
| `escalate` | Not repairable / second failure | Human escalation |
| `block` | Safety violation | Withhold answer |

### Analytics
```
POST /api/v1/analytics/capture   — Record a KPI event (any module)
GET  /api/v1/metrics/summary     — Dashboard KPI aggregation
GET  /api/v1/metrics/export      — Download as JSON or CSV
```

### Audit
```
POST /api/v1/audit/trace         — Lookup audit record by request_id
GET  /api/v1/audit/export        — Download CSV audit log
```

### Feedback
```
POST /api/v1/feedback            — Submit user rating
```

### Health
```
GET /api/v1/health               — Service + dependency health
```

---

## Integration Guide

### Member 1 (Knowledge Service)
Call `/guard/input` before any retrieval to validate the incoming query:

```python
import httpx

response = httpx.post(
    "http://127.0.0.1:8002/api/v1/guard/input",
    json={
        "query": "What are the hand hygiene guidelines?",
        "user_role": "nurse",
        "request_id": "REQ-001",
    },
    timeout=10,
)
result = response.json()
if result["decision"] in ("block", "escalate"):
    # Do not proceed to retrieval
    return result
safe_query = result["safe_query"]  # Use this for Chroma retrieval
```

### Member 2 (Orchestration / LangGraph)
Two integration points in the graph:

**1. `input_guard` node** → call `/guard/input`
**2. `validate_response` node** → call `/guard/output`

Include retrieved chunk texts in `metadata.retrieved_chunks` for grounding checks:

```python
httpx.post(
    "http://127.0.0.1:8002/api/v1/guard/output",
    json={
        "answer": generated_answer,
        "citations": citations,
        "cautions": cautions,
        "risk_level": "low",
        "user_role": user_role,
        "retrieved_document_ids": retrieved_ids,
        "retry_count": retry_count,
        "metadata": {"retrieved_chunks": chunk_texts},
    },
)
```

Emit analytics events at each workflow stage:
```python
httpx.post(
    "http://127.0.0.1:8002/api/v1/analytics/capture",
    json={
        "event_type": "meditrust_llm_invoked",
        "user_role": user_role,
        "properties": {
            "request_id": request_id,
            "model": "gemini-1.5-flash",
            "prompt_tokens": 1200,
            "completion_tokens": 400,
            "llm_latency_ms": 1800,
        },
    },
)
```

### Member 4 (Integration Gateway / Next.js)
- Health check: `GET /api/v1/health` (system-health page)
- Dashboard: `GET /api/v1/metrics/summary` (governance page)
- Feedback: `POST /api/v1/feedback` (after answer delivery)
- Audit: `POST /api/v1/audit/trace` (compliance officer view)

The browser should **never** call governance_service directly.
All calls go through the Member 4 Next.js Route Handler BFF.

---

## Running Tests

```powershell
.\scripts\test_governance.ps1

# With coverage:
.\scripts\test_governance.ps1 -Coverage

# Or manually:
cd governance_service
$env:PYTHONPATH = ".."
python -m pytest tests/ -v --tb=short
```

**Test coverage:**
| Test file | Coverage |
|---|---|
| `test_input_guard.py` | Injection, escalation, redaction, roles, length |
| `test_output_guard.py` | Citation validity, grounding, safety, retry |
| `test_analytics_adapter.py` | Cascade, SQLite, JSONL, metrics |
| `test_api.py` | All endpoints, contract, CORS, error codes |

---

## Architecture

```
POST /guard/input
  └── run_input_guard()
        ├── redact()              ← regex PII/PHI engine
        ├── classify()            ← deterministic risk rules
        └── role_check()

POST /guard/output
  └── run_output_guard()
        ├── schema_check()
        ├── safety_check()        ← clinical advice regex
        ├── validate_citations()  ← hallucination + status + role
        └── check_grounding()     ← NLP coverage ± optional Gemini

POST /analytics/capture
  └── AnalyticsAdapter.capture()
        ├── PostHogClient.capture()    ← try first
        ├── SQLiteStore.insert_event() ← fallback
        └── JSONLStore.append()        ← last resort

GET /metrics/summary
  └── SQLiteStore.get_metrics_summary()
```

---

## Security Checklist

- [ ] `GEMINI_API_KEY` set in `.env` only — never in source
- [ ] `POSTHOG_PROJECT_TOKEN` set in `.env` only — never in source
- [ ] `AUDIT_STORE_RAW_QUERY=false` (default) — query hash only
- [ ] No `NEXT_PUBLIC_` prefix on any secret
- [ ] `.env` added to `.gitignore`
- [ ] Synthetic documents visibly labelled as demonstration-only

---

## Fallback Matrix

| Failure | Fallback | User impact |
|---|---|---|
| PostHog blocked | Write to SQLite | Analytics degraded, workflow unaffected |
| SQLite failure | Append to JSONL | Analytics degraded, workflow unaffected |
| Guardrails package error | Deterministic local validators | Degraded guardrail mode badge |
| Gemini verifier unavailable | Deterministic grounding only | Score may be less precise |
| Service crash | Health endpoint returns 503 | Member 4 shows degraded status |

---

## Environment Variables

See [.env.example](.env.example) for the full list with descriptions.
Critical variables:

| Variable | Required | Default | Notes |
|---|---|---|---|
| `POSTHOG_PROJECT_TOKEN` | No | (empty) | Falls back to SQLite if empty |
| `GEMINI_API_KEY` | No | (empty) | Only needed if `GEMINI_GUARDRAIL_ENABLED=true` |
| `SQLITE_PATH` | Yes | `./storage/audit/meditrust.db` | Auto-created |
| `JSONL_FALLBACK_PATH` | Yes | `./storage/analytics/events.jsonl` | Auto-created |
| `GROUNDING_PASS_THRESHOLD` | Yes | `0.85` | Adjust for precision/recall tradeoff |

---

## Shared Schemas

Other modules import from `shared/schemas/`:

```python
# Member 1, 2, or 4:
from shared.schemas.governance import (
    InputGuardRequest, InputGuardResponse,
    OutputGuardRequest, OutputGuardResponse,
    AnalyticsCaptureRequest, AnalyticsCaptureResponse,
    MetricsSummaryResponse,
    FeedbackRequest, FeedbackResponse,
)
from shared.schemas.common import (
    Citation, RiskLevel, GuardDecision, ValidationStatus,
    TokenMetrics, LatencyMetrics,
)
```

Ensure `PYTHONPATH` includes the repo root so `shared/` resolves correctly.

---

