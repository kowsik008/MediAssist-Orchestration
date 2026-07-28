"""
governance_service/app/config.py
----------------------------------
All configuration is loaded from environment variables (via .env file).
No secrets are hard-coded. Import `settings` wherever config is needed.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    MediTrust AI – Governance Service configuration.
    All values are read from the process environment or a .env file in the
    governance_service/ directory.
    """

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_MODE: str = "integrated"        # "integrated" | "mock"
    SERVICE_NAME: str = "governance-service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_HOST: str = "127.0.0.1"
    SERVICE_PORT: int = 8002
    LOG_LEVEL: str = "INFO"

    # ── CORS (Member 4 Next.js + Member 4 Gateway integration) ───────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://127.0.0.1:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Integration URLs (other members' services) ────────────────────────────
    # Member 1 – Knowledge Service
    KNOWLEDGE_SERVICE_URL: str = "http://127.0.0.1:8001"
    # Member 2 – Orchestration Service
    ORCHESTRATION_SERVICE_URL: str = "http://127.0.0.1:8003"
    # Member 4 – Integration Gateway
    INTEGRATION_API_URL: str = "http://127.0.0.1:8000"

    # ── Guardrails ────────────────────────────────────────────────────────────
    GUARDRAILS_ENABLED: bool = True
    GUARDRAILS_DEGRADED_FALLBACK: bool = True   # Use deterministic if package fails
    MAX_QUERY_LENGTH: int = 4096
    MAX_CONVERSATION_TURNS: int = 20

    # Risk thresholds
    HIGH_RISK_ESCALATION_ENABLED: bool = True
    GROUNDING_PASS_THRESHOLD: float = 0.85
    CITATION_VALIDITY_MIN: float = 0.95

    # Optional Gemini verifier for output grounding
    GEMINI_GUARDRAIL_ENABLED: bool = False
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # ── Analytics ─────────────────────────────────────────────────────────────
    POSTHOG_ENABLED: bool = True
    POSTHOG_PROJECT_TOKEN: str = ""
    POSTHOG_HOST: str = "https://app.posthog.com"
    POSTHOG_TIMEOUT_SECONDS: int = 5
    POSTHOG_LOCAL_FALLBACK: bool = True

    SQLITE_PATH: str = "./storage/audit/meditrust.db"
    JSONL_FALLBACK_PATH: str = "./storage/analytics/events.jsonl"

    # SQLite connection pool
    SQLITE_POOL_SIZE: int = 5
    SQLITE_TIMEOUT_SECONDS: int = 10

    # Metrics aggregation window
    METRICS_WINDOW_HOURS: int = 24

    # ── Audit ─────────────────────────────────────────────────────────────────
    AUDIT_RETAIN_DAYS: int = 90
    AUDIT_STORE_RAW_QUERY: bool = False   # MUST remain False in production

    # ── Regeneration ──────────────────────────────────────────────────────────
    MAX_REGENERATION_ATTEMPTS: int = 1


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# Module-level convenience alias
settings = get_settings()
