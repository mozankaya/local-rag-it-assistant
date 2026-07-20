from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "İZELTAŞ IT Asistanı API"
    environment: str = "development"

    n8n_rag_webhook_url: str
    n8n_feedback_webhook_url: str

    request_timeout_seconds: float = 60.0
    max_question_length: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()