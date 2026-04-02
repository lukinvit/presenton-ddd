"""Presentation domain — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domains.presentation.api.router import create_presentation_router
from shared.infrastructure.config import get_settings
from shared.infrastructure.database import DatabaseConfig, create_engine_from_config
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus


def create_app() -> FastAPI:
    settings = get_settings()

    engine = create_engine_from_config(
        DatabaseConfig(url=settings.database_url)
    )
    event_bus = InMemoryEventBus()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield
        await engine.dispose()

    app = FastAPI(
        title="Presenton — Presentation Domain",
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

    from domains.presentation.domain.repositories import PresentationRepository  # noqa: F401
    from unittest.mock import AsyncMock  # TODO: replace with real SQLModel-backed repo
    repo: PresentationRepository = AsyncMock(spec=PresentationRepository)  # type: ignore[assignment]

    router = create_presentation_router(repo=repo, event_bus=event_bus)
    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "domain": "presentation"}

    return app


app = create_app()
