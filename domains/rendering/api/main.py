"""Rendering domain — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domains.rendering.api.router import create_rendering_router
from domains.rendering.domain.services import HTMLRenderer
from shared.infrastructure.config import get_settings
from shared.infrastructure.database import DatabaseConfig, create_engine_from_config
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus


def create_app() -> FastAPI:
    settings = get_settings()

    engine = create_engine_from_config(DatabaseConfig(url=settings.database_url))
    _event_bus = InMemoryEventBus()  # noqa: F841 — available for future use

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield
        await engine.dispose()

    app = FastAPI(
        title="Presenton — Rendering Domain",
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

    from domains.rendering.domain.repositories import RenderJobRepository
    from unittest.mock import AsyncMock  # TODO: replace with real repo
    repo: RenderJobRepository = AsyncMock(spec=RenderJobRepository)  # type: ignore[assignment]
    html_renderer = HTMLRenderer()

    router = create_rendering_router(repo=repo, html_renderer=html_renderer)
    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "domain": "rendering"}

    return app


app = create_app()
