"""
PitchPilot Application Configuration.

All configuration is loaded from environment variables using Pydantic Settings.
Sensitive values (API keys, secrets) are never logged or exposed.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────
    app_name: str = "PitchPilot"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    secret_key: SecretStr = Field(default=SecretStr("change-me-in-production"))

    # ── CORS ─────────────────────────────────────────────────────
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:3001"]
    )

    # ── Database (Supabase PostgreSQL) ───────────────────────────
    supabase_database_url: str = Field(
        default="postgresql://postgres:password@localhost:5432/pitchpilot",
        description="Supabase PostgreSQL database connection URL",
    )
    db_pool_size: int = Field(default=20, ge=1, le=100)
    db_max_overflow: int = Field(default=10, ge=0, le=50)
    db_pool_timeout: int = Field(default=30, ge=5)
    db_pool_recycle: int = Field(default=1800, ge=300)

    # ── Supabase ─────────────────────────────────────────────────
    supabase_url: str = Field(default="https://your-project.supabase.co")
    supabase_anon_key: SecretStr = Field(default=SecretStr(""))
    supabase_service_role_key: SecretStr = Field(default=SecretStr(""))
    supabase_jwt_secret: SecretStr = Field(default=SecretStr(""))

    # ── Redis (Upstash) ──────────────────────────────────────────
    upstash_redis_rest_url: str = Field(default="")
    upstash_redis_rest_token: SecretStr = Field(default=SecretStr(""))

    # ── OpenAI ───────────────────────────────────────────────────
    openai_api_key: SecretStr = Field(default=SecretStr(""))
    openai_model: str = Field(default="gpt-4o")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    openai_realtime_model: str = Field(default="gpt-4o-realtime-preview")

    # ── Encryption ───────────────────────────────────────────────
    encryption_key: SecretStr = Field(
        default=SecretStr(""),
        description="Fernet encryption key (base64) for API key storage",
    )

    # ── Observability ────────────────────────────────────────────
    langfuse_public_key: str = Field(default="")
    langfuse_secret_key: SecretStr = Field(default=SecretStr(""))
    langfuse_host: str = Field(default="https://cloud.langfuse.com")

    # ── Rate Limiting ────────────────────────────────────────────
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)

    # ── LangGraph ────────────────────────────────────────────────
    langgraph_strict_msgpack: bool = Field(default=True)

    # ── Timeouts ─────────────────────────────────────────────────
    llm_timeout_seconds: int = Field(default=120, ge=10)
    websocket_timeout_seconds: int = Field(default=300, ge=30)
    api_request_timeout_seconds: int = Field(default=30, ge=5)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def database_url_asyncpg(self) -> str:
        """Get database URL formatted for SQLAlchemy asyncpg driver."""
        url = self.supabase_database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def database_url_psycopg(self) -> str:
        """Get database URL formatted for psycopg driver (LangGraph)."""
        url = self.supabase_database_url
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
