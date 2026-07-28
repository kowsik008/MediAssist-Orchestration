from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_mode: str = "integrated"
    service_host: str = "127.0.0.1"
    service_port: int = 8000
    knowledge_service_url: str = "http://127.0.0.1:8001"
    governance_service_url: str = "http://127.0.0.1:8002"
    orchestration_service_url: str = "http://127.0.0.1:8003"
    request_timeout_seconds: float = 45.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
