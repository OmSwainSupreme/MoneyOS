"""Centralized application configuration.

Defines the single source of truth for runtime configuration via
``pydantic-settings``. Values are loaded from environment variables and an
optional ``.env`` file, then validated and coerced to typed fields.

The ``pydantic-settings`` package is the canonical implementation and is
installed in the Docker image (see ``requirements.txt``). A minimal
compatibility shim is used only when the package is unavailable, so the
application can still boot in offline/constrained environments; the shim
exposes the same ``Settings`` surface and is not exercised in production.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Final

# Default database URL uses the asyncpg driver explicitly. Override in
# production via the DATABASE_URL environment variable (also asyncpg).
_DEFAULT_DATABASE_URL: Final[str] = (
    "postgresql+asyncpg://db_user:db_password@localhost:5432/moneyos_db"
)
# Development defaults that must never be used in production.
_INSECURE_DEFAULTS = {
    "database_url": _DEFAULT_DATABASE_URL,
    "secret_key": "",
}


try:  # Preferred production path.
    from pydantic import Field
    from pydantic_settings import BaseSettings, SettingsConfigDict

    _USING_PYDANTIC_SETTINGS = True

    class Settings(BaseSettings):
        """Typed runtime configuration sourced from the environment."""

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="ignore",
        )

        # --- Service identity ---
        project_name: str = Field(default="MoneyOS")
        service_name: str = Field(default="MoneyOS API")
        version: str = Field(default="0.1.0")

        # --- Environment / runtime ---
        environment: str = Field(default="development")
        debug: bool = Field(default=False)
        host: str = Field(default="0.0.0.0")
        port: int = Field(default=8000)
        log_level: str = Field(default="INFO")

        # --- API structure ---
        api_v1_prefix: str = Field(default="/api/v1")

        # --- CORS (configurable middleware) ---
        cors_allow_origins: list[str] = Field(default=["*"])
        cors_allow_credentials: bool = Field(default=False)
        cors_allow_methods: list[str] = Field(default=["*"])
        cors_allow_headers: list[str] = Field(default=["*"])

        # --- Database ---
        # Explicit asyncpg connection string. Override via DATABASE_URL in
        # deployment; the scheme must remain postgresql+asyncpg.
        database_url: str = Field(default=_DEFAULT_DATABASE_URL)
        # Async connection pool tuning.
        db_pool_size: int = Field(default=5)
        db_max_overflow: int = Field(default=10)
        db_pool_timeout: int = Field(default=30)
        db_pool_recycle: int = Field(default=1800)
        db_pool_pre_ping: bool = Field(default=True)
        db_echo: bool = Field(default=False)

        # --- Security (wired in a later phase) ---
        secret_key: str = Field(default="")
        access_token_expire_minutes: int = Field(default=30)

        # --- AI providers (wired in a later phase) ---
        ai_provider: str = Field(default="")
        ai_api_key: str = Field(default="")

        @property
        def is_production(self) -> bool:
            """Return ``True`` when running in a production environment."""
            return self.environment.lower() in {"production", "prod"}

        @property
        def async_database_url(self) -> str:
            """The asyncpg DSN consumed by the async engine.

            The connection string is already asyncpg-explicit (see
            ``database_url``), so this returns it directly.
            """
            return self.database_url

        def validate_production(self) -> None:
            """Fail startup when insecure development defaults are detected.

            Raises:
                RuntimeError: When running in production with the default
                    database URL or an empty ``secret_key``.
            """
            if not self.is_production:
                return
            if self.database_url == _INSECURE_DEFAULTS["database_url"]:
                raise RuntimeError(
                    "Refusing to start in production with the default "
                    "development database URL. Set DATABASE_URL."
                )
            if self.secret_key == _INSECURE_DEFAULTS["secret_key"]:
                raise RuntimeError(
                    "Refusing to start in production with an empty SECRET_KEY."
                )

except ImportError:  # Offline fallback - not used in the Docker image.
    _USING_PYDANTIC_SETTINGS = False
    import os
    from pathlib import Path

    from pydantic import BaseModel, Field

    _DOTENV_PATHS: Final[list[str]] = [".env", ".env.local"]

    def _load_dotenv() -> None:
        for name in _DOTENV_PATHS:
            path = Path(name)
            if not path.is_file():
                continue
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value

    def _env(key: str, default: str) -> str:
        return os.getenv(key, default)

    def _env_bool(key: str, default: bool) -> bool:
        value = os.getenv(key)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _env_int(key: str, default: int) -> int:
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def _env_list(key: str, default: list[str]) -> list[str]:
        value = os.getenv(key)
        if not value:
            return default
        return [i.strip() for i in value.split(",") if i.strip()]

    class Settings(BaseModel):  # type: ignore[no-redef]
        """Offline fallback configuration surface (mirrors BaseSettings)."""

        # --- Service identity ---
        project_name: str = Field(default="MoneyOS")
        service_name: str = Field(default="MoneyOS API")
        version: str = Field(default="0.1.0")

        # --- Environment / runtime ---
        environment: str = Field(default="development")
        debug: bool = Field(default=False)
        host: str = Field(default="0.0.0.0")
        port: int = Field(default=8000)
        log_level: str = Field(default="INFO")

        # --- API structure ---
        api_v1_prefix: str = Field(default="/api/v1")

        # --- CORS (configurable middleware) ---
        cors_allow_origins: list[str] = Field(default=["*"])
        cors_allow_credentials: bool = Field(default=False)
        cors_allow_methods: list[str] = Field(default=["*"])
        cors_allow_headers: list[str] = Field(default=["*"])

        # --- Database ---
        # Explicit asyncpg connection string. Override via DATABASE_URL in
        # deployment; the scheme must remain postgresql+asyncpg.
        database_url: str = Field(default=_DEFAULT_DATABASE_URL)
        # Async connection pool tuning.
        db_pool_size: int = Field(default=5)
        db_max_overflow: int = Field(default=10)
        db_pool_timeout: int = Field(default=30)
        db_pool_recycle: int = Field(default=1800)
        db_pool_pre_ping: bool = Field(default=True)
        db_echo: bool = Field(default=False)

        # --- Security (wired in a later phase) ---
        secret_key: str = Field(default="")
        access_token_expire_minutes: int = Field(default=30)

        # --- AI providers (wired in a later phase) ---
        ai_provider: str = Field(default="")
        ai_api_key: str = Field(default="")

        @property
        def is_production(self) -> bool:
            """Return ``True`` when running in a production environment."""
            return self.environment.lower() in {"production", "prod"}

        @property
        def async_database_url(self) -> str:
            """The asyncpg DSN consumed by the async engine.

            The connection string is already asyncpg-explicit (see
            ``database_url``), so this returns it directly.
            """
            return self.database_url

        def validate_production(self) -> None:
            """Fail startup when insecure development defaults are detected.

            Raises:
                RuntimeError: When running in production with the default
                    database URL or an empty ``secret_key``.
            """
            if not self.is_production:
                return
            if self.database_url == _INSECURE_DEFAULTS["database_url"]:
                raise RuntimeError(
                    "Refusing to start in production with the default "
                    "development database URL. Set DATABASE_URL."
                )
            if self.secret_key == _INSECURE_DEFAULTS["secret_key"]:
                raise RuntimeError(
                    "Refusing to start in production with an empty SECRET_KEY."
                )


def _build_settings() -> Settings:
    """Load environment/dotenv and construct the typed ``Settings``."""
    if not _USING_PYDANTIC_SETTINGS:
        _load_dotenv()
        data: dict[str, Any] = {
            "project_name": _env("PROJECT_NAME", "MoneyOS"),
            "service_name": _env("SERVICE_NAME", "MoneyOS API"),
            "version": _env("VERSION", "0.1.0"),
            "environment": _env("APP_ENV", "development"),
            "debug": _env_bool("DEBUG", False),
            "host": _env("HOST", "0.0.0.0"),
            "port": _env_int("PORT", 8000),
            "log_level": _env("LOG_LEVEL", "INFO"),
            "api_v1_prefix": _env("API_V1_PREFIX", "/api/v1"),
            "cors_allow_origins": _env_list("CORS_ALLOW_ORIGINS", ["*"]),
            "cors_allow_credentials": _env_bool(
                "CORS_ALLOW_CREDENTIALS", False
            ),
            "cors_allow_methods": _env_list("CORS_ALLOW_METHODS", ["*"]),
            "cors_allow_headers": _env_list("CORS_ALLOW_HEADERS", ["*"]),
            "database_url": _env(
                "DATABASE_URL",
                _DEFAULT_DATABASE_URL,
            ),
            "db_pool_size": _env_int("DB_POOL_SIZE", 5),
            "db_max_overflow": _env_int("DB_MAX_OVERFLOW", 10),
            "db_pool_timeout": _env_int("DB_POOL_TIMEOUT", 30),
            "db_pool_recycle": _env_int("DB_POOL_RECYCLE", 1800),
            "db_pool_pre_ping": _env_bool("DB_POOL_PRE_PING", True),
            "db_echo": _env_bool("DB_ECHO", False),
            "secret_key": _env("SECRET_KEY", ""),
            "access_token_expire_minutes": _env_int(
                "ACCESS_TOKEN_EXPIRE_MINUTES", 30
            ),
            "ai_provider": _env("AI_PROVIDER", ""),
            "ai_api_key": _env("AI_API_KEY", ""),
        }
        return Settings(**data)
    return Settings()  # type: ignore[call-arg]


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return _build_settings()
