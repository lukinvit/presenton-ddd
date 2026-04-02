"""Auth domain — FastAPI application entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domains.auth.api.router import create_auth_router
from domains.auth.domain.services import EncryptionService
from shared.infrastructure.config import get_settings
from shared.infrastructure.database import DatabaseConfig, create_engine_from_config
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus


def create_app() -> FastAPI:
    settings = get_settings()

    engine = create_engine_from_config(DatabaseConfig(url=settings.database_url))
    event_bus = InMemoryEventBus()

    encryption_key = settings.encryption_key or os.getenv("PRESENTON_ENCRYPTION_KEY", "")
    encryption_service = EncryptionService(key=encryption_key)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield
        await engine.dispose()

    app = FastAPI(
        title="Presenton — Auth Domain",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from domains.auth.domain.repositories import OAuthConnectionRepository, OAuthStateRepository
    from unittest.mock import AsyncMock  # TODO: replace with real repos
    state_repo: OAuthStateRepository = AsyncMock(spec=OAuthStateRepository)  # type: ignore[assignment]
    connection_repo: OAuthConnectionRepository = AsyncMock(spec=OAuthConnectionRepository)  # type: ignore[assignment]

    # No OAuth providers configured by default — add adapters here as needed
    oauth_adapters: dict = {}

    router = create_auth_router(
        oauth_adapters=oauth_adapters,
        state_repo=state_repo,
        connection_repo=connection_repo,
        encryption_service=encryption_service,
        event_bus=event_bus,
    )
    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "domain": "auth"}

    return app


app = create_app()
