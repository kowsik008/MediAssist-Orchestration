# MediTrust AI Integrated MVP

This folder is the combined four-member build for the governed healthcare
knowledge assistant. It follows the final repository blueprint and runs
locally without Docker or external tunnelling.

## Services

| Component | URL | Purpose |
|---|---|---|
| Next.js frontend | `http://127.0.0.1:3000` | Browser UI and BFF routes |
| Integration gateway | `http://127.0.0.1:8000` | Stable public backend contract |
| Knowledge service | `http://127.0.0.1:8001` | Chroma RAG and semantic cache |
| Governance service | `http://127.0.0.1:8002` | Guards, audit, analytics and KPI |
| Orchestration service | `http://127.0.0.1:8003` | Workflow, providers and optimization |
| Headroom proxy | `http://127.0.0.1:8787` | Optional native optimization proxy |

## Setup

From this folder:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

The setup creates isolated Python virtual environments for each service. This
avoids dependency conflicts between member modules. Headroom is optional and
does not block the MVP:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1 -WithHeadroom
```

Use `-WithHeadroom` only on a Windows machine with Rust/Cargo and Visual C++
Build Tools installed.

## Run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_all.ps1
```

Ingest the knowledge corpus once:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ingest.ps1
```

Check dependencies:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\health_check.ps1
```

Stop managed processes:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\stop_all.ps1
```

## Test

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\test_all.ps1
```

The suite covers each member module plus gateway contract checks and the
Next.js lint/production build.

## Integrated Flow

`Browser -> Next.js BFF -> Gateway -> Orchestration -> Governance input guard
-> Knowledge cache/RAG -> Headroom or deterministic fallback -> Gemini/mock
provider -> Governance output guard -> validated cache write -> analytics`

The browser never calls Python services directly. High-risk, blocked and
insufficient-evidence requests stop before unrestricted generation.

## Configuration

- Root `.env`: knowledge and storage configuration
- `governance_service/.env`: guardrails and local analytics fallback
- `orchestration_service/.env`: Gemini/provider and Headroom settings
- `integration_api/.env`: internal service URLs
- `frontend/.env.local`: server-only gateway URL and public UI flags

No real credentials are included. Set `GEMINI_API_KEY` and PostHog values only
in local environment files. Keep all secret values away from `NEXT_PUBLIC_`.

## Lab Fallbacks

- Headroom unavailable: deterministic context optimization
- Gemini unavailable: mock/evidence-safe provider mode
- PostHog unavailable: SQLite, then JSONL
- Chroma cache unavailable: normal retrieval
- Knowledge unavailable: no model generation through the integrated gateway
- Governance analytics unavailable: workflow trace records the capture failure
