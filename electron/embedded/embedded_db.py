"""SQLite database configuration for Electron mode.

All domains share one SQLite file located in the OS-specific user-data
directory (passed in via the PRESENTON_DB_PATH environment variable).

Usage:
    from embedded.embedded_db import get_electron_db_config, get_shared_engine

    config = get_electron_db_config()   # reads PRESENTON_DB_PATH from env
    engine = get_shared_engine()        # cached AsyncEngine singleton
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine

from shared.infrastructure.database import DatabaseConfig, create_engine_from_config


def get_electron_db_config(app_data_dir: str | None = None) -> DatabaseConfig:
    """Return a DatabaseConfig pointing at the Electron SQLite database.

    Priority:
      1. Explicit ``app_data_dir`` argument.
      2. ``PRESENTON_DB_PATH`` environment variable (full path to .db file).
      3. Fallback: ``presenton.db`` in the current working directory.
    """
    if app_data_dir is not None:
        db_path = Path(app_data_dir) / "presenton.db"
    elif db_env := os.getenv("PRESENTON_DB_PATH"):
        db_path = Path(db_env)
    else:
        db_path = Path.cwd() / "presenton.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return DatabaseConfig(url=f"sqlite+aiosqlite:///{db_path}")


@lru_cache(maxsize=1)
def get_shared_engine() -> AsyncEngine:
    """Return the singleton AsyncEngine for the Electron SQLite database."""
    config = get_electron_db_config()
    return create_engine_from_config(config)
