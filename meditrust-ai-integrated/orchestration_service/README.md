# Orchestration Service

This service owns Member 2's execution scope:

- shared graph state and trace-event contracts
- deterministic intent and risk classification
- controlled LangGraph-style orchestration flow
- Gemini, mock, and unavailable model providers
- prompt template selection
- Headroom adapter and deterministic optimization fallback
- orchestration metrics and health endpoints
- direct integration with Member 1 knowledge-service cache and retrieval APIs
- direct integration with Member 3 governance input/output guard and analytics APIs

## Environment

Configuration is read only from `.env`.

Example:

```env
ORCHESTRATION_ENV=dev
ORCHESTRATION_HOST=127.0.0.1
ORCHESTRATION_PORT=8011
MODEL_PROVIDER=mock
GEMINI_MODEL=gemini-2.5-flash
GEMINI_API_KEY=
HEADROOM_ENABLED=false
HEADROOM_AVAILABLE=false
HEADROOM_API_KEY=
MAX_REGENERATIONS=1
```

The orchestration service expects:

- Member 1 knowledge service at `KNOWLEDGE_SERVICE_BASE_URL`, default `http://127.0.0.1:8001`
- Member 3 governance service at `GOVERNANCE_SERVICE_BASE_URL`, default `http://127.0.0.1:8002`

## Endpoints

- `GET /health`
- `POST /api/v1/invoke/baseline`
- `POST /api/v1/invoke/optimized`
- `POST /api/v1/invoke/classify`
- `GET /api/v1/examples`

## Integration Flow

For allowed requests, the service now integrates with Member 1 in this order:

1. governance input guard via `POST /api/v1/guard/input`
2. deterministic risk classification
3. semantic cache lookup via `POST /cache/lookup`
4. evidence retrieval via `POST /retrieve` when cache misses
5. safe fallback when `evidence_status` is `insufficient`
6. context optimization and provider generation only when evidence is sufficient
7. governance output guard via `POST /api/v1/guard/output`
8. governance analytics capture at major workflow stages

## Headroom CLI

The optimized path can use the Headroom CLI proxy when enabled.

1. Install native prerequisites on Windows:
   - Rust/Cargo
   - Visual Studio Build Tools with `Desktop development with C++`
2. From the repo root, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\orchestration_service\scripts\setup_headroom_windows.ps1
```

3. To install and immediately start the proxy:

```powershell
powershell -ExecutionPolicy Bypass -File .\orchestration_service\scripts\setup_headroom_windows.ps1 -StartProxy
```

4. If Headroom is already installed and you only need the proxy:

```powershell
powershell -ExecutionPolicy Bypass -File .\orchestration_service\scripts\start_headroom_proxy.ps1
```

5. Verify the proxy:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8787/health
```

6. Restart the orchestration service after setup so `/health` reflects the new Headroom availability.

When the proxy is reachable, the adapter calls `POST /v1/compress` and preserves source IDs through the optimized context selection. If the proxy is unavailable, deterministic fallback optimization is used.

### Native Windows Notes

- The setup script checks for `cargo.exe` and `link.exe` before attempting installation.
- If `link.exe` is missing, install Visual Studio Build Tools and include the C++ workload.
- The script updates [`.env`](C:/Users/joyas/OneDrive/Documents/MediAssist/orchestration_service/.env) to enable Headroom and point the service at `http://127.0.0.1:8787`.
- The service will still fall back deterministically if the proxy is down at runtime.

## Notes

- Gemini is only used for ambiguous intent and risk classification.
- The optimized flow preserves source IDs, warnings, negative statements, and escalation text.
- When Headroom is unavailable, deterministic context optimization is used.
