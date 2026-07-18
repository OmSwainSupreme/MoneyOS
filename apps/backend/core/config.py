"""Application configuration.

Loads settings from environment variables with sane defaults.
Single source of configuration for the backend.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict


class Settings:
    """Runtime settings, sourced from the environment."""

    def __init__(self) -> None:
        self.project_name: str = os.getenv("PROJECT_NAME", "MoneyOS")
        self.environment: str = os.getenv("APP_ENV", "development")
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"

        self.database_url: str = os.getenv(
            "DATABASE_URL",
            "postgresql://db_user:db_password@localhost:5432/moneyos_db",
        )
        self.api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api/v1")

        # Security
        self.secret_key: str = os.getenv("SECRET_KEY", "")
        self.access_token_expire_minutes: int = int(
            os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
        )

        # AI (placeholder — providers wired in Phase 1+)
        self.ai_provider: str = os.getenv("AI_PROVIDER", "")
        self.ai_api_key: str = os.getenv("AI_API_KEY", "")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "environment": self.environment,
            "debug": self.debug,
            "api_v1_prefix": self.api_v1_prefix,
        }


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor."""
    return Settings()


settings = get_settings()
