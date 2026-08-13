from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "İZELTAŞ IT Asistanı API"
    environment: str = "development"

    n8n_rag_webhook_url: str
    n8n_feedback_webhook_url: str
    n8n_reindex_webhook_url: str | None = None
    n8n_webhook_secret: str

    n8n_health_url: str = "http://localhost:5678/healthz"
    ollama_health_url: str = "http://localhost:11434/api/tags"

    request_timeout_seconds: float = 60.0
    reindex_timeout_seconds: float = 300.0
    service_status_timeout_seconds: float = 3.0
    max_question_length: int = 1000

    rag_top_k: int = Field(
        default=5,
        ge=1,
        le=50,
    )
    rag_score_threshold: float = Field(
        default=0.54,
        ge=0.0,
        le=2.0,
    )
    rag_max_sources: int = Field(
        default=3,
        ge=1,
        le=10,
    )

    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
