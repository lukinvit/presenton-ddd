"""Auth domain — FastAPI application entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from domains.auth.api.router import create_auth_router
from domains.auth.domain.services import EncryptionService
from domains.auth.infrastructure.connection_store import InMemoryConnectionStore
from shared.infrastructure.config import get_settings
from shared.infrastructure.database import DatabaseConfig, create_engine_from_config
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus


class StoreApiKeyRequest(BaseModel):
    provider: str
    api_key: str


def create_app() -> FastAPI:
    settings = get_settings()

    engine = create_engine_from_config(DatabaseConfig(url=settings.database_url))
    event_bus = InMemoryEventBus()

    encryption_key = settings.encryption_key or os.getenv("PRESENTON_ENCRYPTION_KEY", "")
    encryption_service = EncryptionService(key=encryption_key)
    connection_store = InMemoryConnectionStore(encryption_service=encryption_service)

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

    # --- API Key connection endpoints ---
    # Gateway routes /api/v1/auth/* → auth domain /api/v1/auth/*

    @app.post("/api/v1/auth/connect/api-key")
    async def store_api_key(req: StoreApiKeyRequest) -> dict:
        allowed_providers = {"anthropic", "openai", "google", "ollama"}
        if req.provider not in allowed_providers:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {req.provider}")
        if not req.api_key.strip():
            raise HTTPException(status_code=422, detail="api_key must not be empty")
        connection_store.store_key(req.provider, req.api_key.strip())
        return {"status": "connected", "provider": req.provider}

    @app.get("/api/v1/auth/connections")
    async def list_connections() -> list[dict]:
        return connection_store.list_connections()

    @app.post("/api/v1/auth/disconnect/{provider}")
    async def disconnect_provider(provider: str) -> dict:
        connection_store.disconnect(provider)
        return {"status": "disconnected", "provider": provider}

    # ---

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "domain": "auth"}

    return app


app = create_app()
