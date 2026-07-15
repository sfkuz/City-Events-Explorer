from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )
    tg_bot_token: str = Field(alias="TG_BOT_TOKEN")
    app_name: str = "user-app"
    app_env: str = "dev"
    log_level: str = "INFO"

    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    db_pool_min_size: int = 1
    db_pool_max_size: int = 10
    db_connect_timeout_seconds: float = 5.0


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    return Settings()