"""
Application configuration.

All configuration is loaded from environment variables (optionally via a
`.env` file). Nothing sensitive is hardcoded here — see `.env.example` for
the full list of supported variables.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings, populated from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────
    app_name: str = "Welfare Management System"
    app_version: str = "2.0.0"
    environment: str = "development"
    debug: bool = False

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./welfare.db"

    # ── Security / JWT ───────────────────────────────────────────────────
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # ── CORS ─────────────────────────────────────────────────────────────
    cors_origins: str = "*"

    # ── Default admin bootstrap ──────────────────────────────────────────
    admin_email: str
    admin_password: str
    admin_full_name: str = "System Admin"

    # ── SMTP / Email ─────────────────────────────────────────────────────
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_sender_email: str = ""
    smtp_password: str = ""

    @property
    def cors_origin_list(self) -> List[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (loaded once per process)."""
    return Settings()


settings = get_settings()
