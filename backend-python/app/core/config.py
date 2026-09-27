from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = (
    BACKEND_ROOT.parent if (BACKEND_ROOT.parent / "frontend").is_dir() else BACKEND_ROOT
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TrainFlow AI"
    frontend_url: AnyHttpUrl = AnyHttpUrl("http://localhost:3000")
    backend_url: AnyHttpUrl = AnyHttpUrl("http://localhost:8000")
    database_url: str = ""
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    auth_cookie_secure: bool = False
    cv_storage_dir: Path = PROJECT_ROOT / "storage" / "cv"
    max_cv_file_size_mb: int = 10
    document_storage_path: Path = PROJECT_ROOT / "storage" / "documents"
    document_max_size_mb: int = 10
    local_llm_url: str | None = None
    local_llm_model: str | None = None
    cv_llm_model: str | None = None
    cv_llm_max_tokens: int = 1024
    cv_llm_max_input_chars: int = 8000
    cv_llm_keep_alive: str = "30s"
    local_llm_timeout_seconds: int = 600
    local_llm_max_tokens: int = 4096
    local_llm_temperature: float = 0
    local_llm_keep_alive: str = "1h"
    local_llm_num_ctx: int = 8192
    local_llm_num_thread: int = 6
    local_llm_num_batch: int = 512
    seed_demo_data: bool = False
    demo_admin_email: str | None = None
    demo_admin_password: str | None = None

    @model_validator(mode="after")
    def validate_required_secrets(self) -> "Settings":
        if not self.database_url.strip():
            raise ValueError("DATABASE_URL doit être configurée.")
        if len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET doit contenir au moins 32 caractères.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
