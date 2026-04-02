from shared.infrastructure.database import DatabaseConfig, create_engine_from_config


class TestDatabaseConfig:
    def test_default_sqlite_config(self) -> None:
        config = DatabaseConfig(url="sqlite+aiosqlite:///test.db")
        assert config.url == "sqlite+aiosqlite:///test.db"
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.pool_recycle == 3600

    def test_postgres_config(self) -> None:
        config = DatabaseConfig(
            url="postgresql+asyncpg://user:pass@localhost/db",
            pool_size=20,
            max_overflow=40,
        )
        assert config.pool_size == 20
        assert config.max_overflow == 40

    def test_schema_config(self) -> None:
        config = DatabaseConfig(
            url="postgresql+asyncpg://user:pass@localhost/db",
            schema="presentation",
        )
        assert config.schema == "presentation"


class TestCreateEngine:
    def test_creates_engine_for_sqlite(self) -> None:
        config = DatabaseConfig(url="sqlite+aiosqlite:///test.db")
        engine = create_engine_from_config(config)
        assert engine is not None
        assert str(engine.url) == "sqlite+aiosqlite:///test.db"

    def test_creates_engine_for_postgres(self) -> None:
        config = DatabaseConfig(
            url="postgresql+asyncpg://user:pass@localhost/presenton",
            schema="presentation",
        )
        engine = create_engine_from_config(config)
        assert engine is not None
