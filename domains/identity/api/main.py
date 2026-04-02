"""Identity domain — FastAPI application entry point."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domains.identity.api.router import create_identity_router
from domains.identity.domain.services import TokenService
from shared.infrastructure.config import get_settings
from shared.infrastructure.database import DatabaseConfig, create_engine_from_config
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus


def create_app() -> FastAPI:
    settings = get_settings()

    engine = create_engine_from_config(DatabaseConfig(url=settings.database_url))
    event_bus = InMemoryEventBus()

    # JWT token service — expects RSA PEM keys via env
    private_key = os.getenv("PRESENTON_JWT_PRIVATE_KEY", settings.jwt_secret)
    public_key = os.getenv("PRESENTON_JWT_PUBLIC_KEY", settings.jwt_secret)
    token_service = TokenService(
        private_key=private_key,
        public_key=public_key,
        algorithm=settings.jwt_algorithm,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield
        await engine.dispose()

    app = FastAPI(
        title="Presenton — Identity Domain",
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

    from domains.identity.domain.repositories import UserRepository  # noqa: F401
    from unittest.mock import AsyncMock  # TODO: replace with real SQLModel-backed repo
    user_repo: UserRepository = AsyncMock(spec=UserRepository)  # type: ignore[assignment]

    router = create_identity_router(
        user_repo=user_repo,
        event_bus=event_bus,
        token_service=token_service,
    )
    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "domain": "identity"}

    return app


app = create_app()
