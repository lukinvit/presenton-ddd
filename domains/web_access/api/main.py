"""Web Access domain — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domains.web_access.api.router import create_web_access_router
from shared.infrastructure.config import get_settings
from shared.infrastructure.database import DatabaseConfig, create_engine_from_config
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus


def create_app() -> FastAPI:
    settings = get_settings()

    engine = create_engine_from_config(DatabaseConfig(url=settings.database_url))
    event_bus = InMemoryEventBus()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield
        await engine.dispose()

    app = FastAPI(
        title="Presenton — Web Access Domain",
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

    from domains.web_access.domain.repositories import WebQueryRepository
    from domains.web_access.domain.services import ScreenshotAdapter, WebFetchAdapter, WebSearchAdapter
    from unittest.mock import AsyncMock  # TODO: replace with real adapters + repo
    search_adapter: WebSearchAdapter = AsyncMock(spec=WebSearchAdapter)  # type: ignore[assignment]
    fetch_adapter: WebFetchAdapter = AsyncMock(spec=WebFetchAdapter)  # type: ignore[assignment]
    screenshot_adapter: ScreenshotAdapter = AsyncMock(spec=ScreenshotAdapter)  # type: ignore[assignment]
    query_repo: WebQueryRepository = AsyncMock(spec=WebQueryRepository)  # type: ignore[assignment]

    router = create_web_access_router(
        search_adapter=search_adapter,
        fetch_adapter=fetch_adapter,
        screenshot_adapter=screenshot_adapter,
        query_repo=query_repo,
        event_bus=event_bus,
    )
    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "domain": "web_access"}

    return app


app = create_app()
