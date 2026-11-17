"""Application Configuration Module for InferX."""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the repository (parent of backend)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Central configuration for InferX control plane and backend runtime."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Metadata
    APP_NAME: str = "InferX"
    APP_ENV: str = "development"
    VERSION: str = "0.4.2"
    DEBUG: bool = False

    # Server Bindings
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Data Infrastructure
    DATABASE_URL: str = "postgresql+psycopg://inferx:change_me@localhost:5432/inferx"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Inference Engine Integration
    VLLM_BASE_URL: Optional[str] = None
    VLLM_API_KEY: Optional[str] = None

    # Security & Authentication
    JWT_SECRET_KEY: str = "inferx-super-secret-jwt-key-2026-production-change"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEFAULT_RATE_LIMIT_RPS: int = 50

    # Security & CORS
    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
        ]
    )

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"  # "console" | "json"

    @property
    def is_development(self) -> bool:
        """Check if environment is development."""
        return self.APP_ENV.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if environment is production."""
        return self.APP_ENV.lower() == "production"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings."""
    return Settings()
