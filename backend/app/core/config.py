from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    jwt_secret: str = "change-me"
    geoip_db_path: str | None = None

    # NEW: allow setting one or more frontend origins (comma-separated)
    frontend_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()