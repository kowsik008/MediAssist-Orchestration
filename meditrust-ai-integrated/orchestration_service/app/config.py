from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    orchestration_env: str = Field(default="dev", alias="ORCHESTRATION_ENV")
    orchestration_host: str = Field(default="127.0.0.1", alias="ORCHESTRATION_HOST")
    orchestration_port: int = Field(default=8003, alias="ORCHESTRATION_PORT")
    knowledge_service_base_url: str = Field(default="http://127.0.0.1:8001", alias="KNOWLEDGE_SERVICE_BASE_URL")
    governance_service_base_url: str = Field(default="http://127.0.0.1:8002", alias="GOVERNANCE_SERVICE_BASE_URL")

    model_provider: str = Field(default="unavailable", alias="MODEL_PROVIDER")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")

    headroom_enabled: bool = Field(default=False, alias="HEADROOM_ENABLED")
    headroom_available: bool = Field(default=False, alias="HEADROOM_AVAILABLE")
    headroom_api_key: str = Field(default="", alias="HEADROOM_API_KEY")
    headroom_base_url: str = Field(default="http://127.0.0.1:8787", alias="HEADROOM_BASE_URL")
    headroom_cli_path: str = Field(default="headroom", alias="HEADROOM_CLI_PATH")
    headroom_auto_start: bool = Field(default=False, alias="HEADROOM_AUTO_START")
    headroom_proxy_host: str = Field(default="127.0.0.1", alias="HEADROOM_PROXY_HOST")
    headroom_proxy_port: int = Field(default=8787, alias="HEADROOM_PROXY_PORT")
    headroom_model: str = Field(default="gpt-4.1-mini", alias="HEADROOM_MODEL")
    headroom_target_api_url: str = Field(default="", alias="HEADROOM_TARGET_API_URL")
    headroom_default_role: str = Field(default="doctor", alias="HEADROOM_DEFAULT_ROLE")

    max_regenerations: int = Field(default=1, alias="MAX_REGENERATIONS")
    ambiguous_threshold: float = Field(default=0.55, alias="AMBIGUOUS_THRESHOLD")
    request_timeout_seconds: float = Field(default=20.0, alias="REQUEST_TIMEOUT_SECONDS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
