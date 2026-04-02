from __future__ import annotations
from dataclasses import dataclass
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

@dataclass
class DatabaseConfig:
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    schema: str | None = None

def create_engine_from_config(config: DatabaseConfig) -> AsyncEngine:
    is_sqlite = config.url.startswith("sqlite")
    connect_args: dict = {}
    kwargs: dict = {}
    if is_sqlite:
        connect_args["check_same_thread"] = False
    else:
        kwargs["pool_size"] = config.pool_size
        kwargs["max_overflow"] = config.max_overflow
        kwargs["pool_recycle"] = config.pool_recycle
    engine = create_async_engine(config.url, connect_args=connect_args, **kwargs)
    if config.schema and not is_sqlite:
        @event.listens_for(engine.sync_engine, "connect")
        def set_search_path(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute(f"SET search_path TO {config.schema}, public")
            cursor.close()
    return engine
