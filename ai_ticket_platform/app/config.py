from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent
VAR_DIR = BASE_DIR / "var"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "AI Ticket Platform"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    host: str = "0.0.0.0"
    port: int = 8000

    secret_key: str
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "ai_ticket_platform"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    database_url: str

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    redis_url: str

    openai_api_key: str
    openai_model: str = "gpt-4.1-mini"
    openai_embedding_model: str = "text-embedding-3-small"

    vector_db_provider: str = "pgvector"

    upload_dir: Path = VAR_DIR / "data" / "uploads"
    processed_dir: Path = VAR_DIR / "data" / "processed"
    model_dir: Path = VAR_DIR / "data" / "models"

    max_file_size_mb: int = 50

    log_level: str = "INFO"
    log_dir: Path = VAR_DIR / "log"

    celery_broker_url: str
    celery_result_backend: str

    backend_cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
    ]

    classifier_model_path: Path = (
        VAR_DIR / "data" / "models" / "ticket_classifier.pkl"
    )

    chunk_size: int = 1000
    chunk_overlap: int = 200

    top_k_results: int = 5

    enable_telemetry: bool = False

    @field_validator(
        "upload_dir",
        "processed_dir",
        "model_dir",
        "log_dir",
        mode="before",
    )
    @classmethod
    def validate_paths(cls, value: str | Path) -> Path:
        path = Path(value)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]

        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
