from __future__ import annotations

import os
from dataclasses import dataclass

_settings_instance: Settings | None = None


@dataclass
class Settings:
    environment: str = "development"
    log_json: bool = False
    redis_url: str = "redis://localhost:6379"
    database_url: str = "sqlite+aiosqlite:///presenton.db"
    encryption_key: str = ""
    allowed_origins: str = "http://localhost:3000"
    jwt_secret: str = ""
    jwt_algorithm: str = "RS256"
    app_data_directory: str = "./app_data"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            environment=os.getenv("PRESENTON_ENV", "development"),
            log_json=os.getenv("PRESENTON_LOG_JSON", "false").lower() == "true",
            redis_url=os.getenv("PRESENTON_REDIS_URL", "redis://localhost:6379"),
            database_url=os.getenv("PRESENTON_DATABASE_URL", "sqlite+aiosqlite:///presenton.db"),
            encryption_key=os.getenv("PRESENTON_ENCRYPTION_KEY", ""),
            allowed_origins=os.getenv("PRESENTON_ALLOWED_ORIGINS", "http://localhost:3000"),
            jwt_secret=os.getenv("PRESENTON_JWT_SECRET", ""),
            jwt_algorithm=os.getenv("PRESENTON_JWT_ALGORITHM", "RS256"),
            app_data_directory=os.getenv("PRESENTON_APP_DATA_DIR", "./app_data"),
        )


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings.from_env()
    return _settings_instance


def reset_settings() -> None:
    global _settings_instance
    _settings_instance = None
