from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "PhishGuard"
    environment: str = "development"
    api_prefix: str = "/api"

    database_url: str = "sqlite:///./phishguard.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_origin_regex: str | None = r"^(chrome-extension|moz-extension)://[A-Za-z0-9_-]+$"

    jwt_secret: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    admin_username: str = "admin"
    admin_password: str = "phishguard-admin"

    rate_limit_per_minute: int = 120
    model_path: Path = (
        Path(__file__).resolve().parents[1]
        / "services"
        / "ml_engine"
        / "models"
        / "phishing_model.pkl"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PHISHGUARD_",
        extra="ignore",
        protected_namespaces=("settings_",),
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
