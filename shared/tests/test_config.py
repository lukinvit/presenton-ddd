import pytest

from shared.infrastructure.config import Settings, get_settings, reset_settings


class TestSettings:
    def setup_method(self) -> None:
        reset_settings()

    def test_default_settings(self) -> None:
        settings = Settings()
        assert settings.environment == "development"
        assert settings.log_json is False
        assert settings.redis_url == "redis://localhost:6379"
        assert settings.database_url == "sqlite+aiosqlite:///presenton.db"

    def test_settings_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRESENTON_ENV", "production")
        monkeypatch.setenv("PRESENTON_LOG_JSON", "true")
        monkeypatch.setenv("PRESENTON_REDIS_URL", "redis://redis:6379")
        monkeypatch.setenv("PRESENTON_DATABASE_URL", "postgresql+asyncpg://u:p@pg/db")
        monkeypatch.setenv("PRESENTON_ENCRYPTION_KEY", "supersecretkey32bytes000000000000")
        settings = Settings.from_env()
        assert settings.environment == "production"
        assert settings.log_json is True
        assert settings.redis_url == "redis://redis:6379"
        assert settings.database_url == "postgresql+asyncpg://u:p@pg/db"
        assert settings.encryption_key == "supersecretkey32bytes000000000000"

    def test_get_settings_returns_singleton(self) -> None:
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
