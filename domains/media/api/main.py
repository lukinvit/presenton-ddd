"""Media domain — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domains.media.api.router import create_media_router
from shared.infrastructure.config import get_settings
from shared.infrastructure.database import DatabaseConfig, create_engine_from_config
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus


def create_app() -> FastAPI:
    settings = get_settings()

    engine = create_engine_from_config(DatabaseConfig(url=settings.database_url))
    _event_bus = InMemoryEventBus()  # noqa: F841

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield
        await engine.dispose()

    app = FastAPI(
        title="Presenton — Media Domain",
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

    from domains.media.domain.repositories import InfographicTemplateRepository, MediaAssetRepository
    from domains.media.domain.adapters import ImageGenerationAdapter, ImageSearchAdapter
    from unittest.mock import AsyncMock  # TODO: replace with real repos + adapters
    asset_repo: MediaAssetRepository = AsyncMock(spec=MediaAssetRepository)  # type: ignore[assignment]
    template_repo: InfographicTemplateRepository = AsyncMock(spec=InfographicTemplateRepository)  # type: ignore[assignment]
    image_search_adapter: ImageSearchAdapter = AsyncMock(spec=ImageSearchAdapter)  # type: ignore[assignment]
    image_generation_adapter: ImageGenerationAdapter = AsyncMock(spec=ImageGenerationAdapter)  # type: ignore[assignment]

    router = create_media_router(
        asset_repo=asset_repo,
        template_repo=template_repo,
        image_search_adapter=image_search_adapter,
        image_generation_adapter=image_generation_adapter,
    )
    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "domain": "media"}

    return app


app = create_app()
