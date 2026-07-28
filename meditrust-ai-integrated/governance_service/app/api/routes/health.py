"""
governance_service/app/api/routes/health.py
---------------------------------------------
GET /api/v1/health

Checks all dependencies and returns a structured health report.
Consumed by:
  - Member 4 (Integration Gateway) for system-health page
  - Docker-equivalent readiness checks (local: curl 127.0.0.1:8002/api/v1/health)
"""

from __future__ import annotations

import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from governance_service.app.analytics.adapter import analytics_adapter
from governance_service.app.config import settings

router = APIRouter()

_START_TIME = time.time()


@router.get("/health", summary="Governance service health check")
async def health_check() -> JSONResponse:
    """
    Returns HTTP 200 when healthy, HTTP 503 when any critical dependency
    is unavailable.
    """
    backends = analytics_adapter.backend_status()
    sqlite_ok = backends["sqlite"]["available"]
    posthog_ok = backends["posthog"]["available"]
    jsonl_ok = backends["jsonl"]["available"]

    # At least one analytics backend must be available
    analytics_ok = sqlite_ok or posthog_ok or jsonl_ok

    status = "healthy" if analytics_ok else "degraded"
    http_code = 200 if status == "healthy" else 503

    payload = {
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "status": status,
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "mode": settings.APP_MODE,
        "dependencies": [
            {
                "name": "posthog",
                "status": "ok" if posthog_ok else "unavailable",
                "mode": "integrated" if posthog_ok else "fallback",
                "detail": backends["posthog"].get("last_failure"),
            },
            {
                "name": "sqlite",
                "status": "ok" if sqlite_ok else "unavailable",
                "mode": "integrated" if sqlite_ok else "unavailable",
                "detail": backends["sqlite"]["path"],
            },
            {
                "name": "jsonl_fallback",
                "status": "ok" if jsonl_ok else "unavailable",
                "mode": "fallback" if jsonl_ok else "unavailable",
                "detail": backends["jsonl"]["path"],
            },
            {
                "name": "guardrails",
                "status": "ok",
                "mode": "deterministic",
                "detail": "Deterministic guardrails always available",
            },
            {
                "name": "gemini_verifier",
                "status": "ok" if settings.GEMINI_GUARDRAIL_ENABLED and settings.GEMINI_API_KEY else "disabled",
                "mode": "integrated" if settings.GEMINI_GUARDRAIL_ENABLED else "disabled",
            },
        ],
    }

    return JSONResponse(content=payload, status_code=http_code)
