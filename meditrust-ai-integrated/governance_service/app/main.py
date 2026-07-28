"""
governance_service/app/main.py
--------------------------------
MediTrust AI — Governance Service
FastAPI application entry point.

Runs at: http://127.0.0.1:8002
API docs: http://127.0.0.1:8002/docs  (OpenAPI)
Health:   http://127.0.0.1:8002/api/v1/health

INTEGRATION
-----------
Member 1 (Knowledge):   POST /api/v1/guard/input   (before retrieval)
Member 2 (Orchestration): POST /api/v1/guard/input, POST /api/v1/guard/output,
                          POST /api/v1/analytics/capture
Member 4 (Gateway/Frontend): GET /api/v1/health, GET /api/v1/metrics/summary,
                              POST /api/v1/feedback, GET /api/v1/audit/export
"""

from __future__ import annotations

import sys
import time
import traceback
from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from governance_service.app.api.routes import analytics, audit, feedback, guard, health
from governance_service.app.config import settings
from governance_service.app.utils.logger import get_logger

log = get_logger(__name__)

_START_TIME = time.time()


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    log.info(
        "Governance service starting",
        extra={
            "mode": settings.APP_MODE,
            "env": settings.APP_ENV,
            "version": settings.SERVICE_VERSION,
            "port": settings.SERVICE_PORT,
        },
    )
    yield
    log.info("Governance service shutting down.")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="MediTrust AI — Governance Service",
    description=(
        "Provides input/output guardrails, KPI analytics cascade "
        "(PostHog → SQLite → JSONL), citation validation, grounding checks, "
        "audit trail and feedback for the MediTrust AI system.\n\n"
        "**Responsible-use boundary**: This service enforces safety rules but "
        "does not replace clinical judgment."
    ),
    version=settings.SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS (Member 4 Next.js + Gateway) ────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Request logging middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        log.error(
            "Unhandled exception in request",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        )

    latency = int((time.perf_counter() - start) * 1000)
    log.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "latency_ms": latency,
        },
    )
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error("Global exception handler triggered", extra={"error": str(exc)})
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again.",
        },
    )


# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(health.router,    prefix=API_PREFIX, tags=["Health"])
app.include_router(guard.router,     prefix=API_PREFIX, tags=["Guardrails"])
app.include_router(analytics.router, prefix=API_PREFIX, tags=["Analytics"])
app.include_router(feedback.router,  prefix=API_PREFIX, tags=["Feedback"])
app.include_router(audit.router,     prefix=API_PREFIX, tags=["Audit"])


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "MediTrust AI — Governance Service",
        "version": settings.SERVICE_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": f"{API_PREFIX}/health",
        "uptime_seconds": round(time.time() - _START_TIME, 1),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "governance_service.app.main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.APP_ENV == "development",
        log_level=settings.LOG_LEVEL.lower(),
    )
