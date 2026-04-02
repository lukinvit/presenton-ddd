"""Content domain — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domains.content.api.router import create_content_router
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
        title="Presenton — Content Domain",
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

    from domains.content.domain.repositories import (
        ContentPlanRepository,
        SlideContentRepository,
        SystemPromptRepository,
    )
    from domains.content.domain.services import LLMAdapter
    from unittest.mock import AsyncMock  # TODO: replace with real repos + LLM adapter
    plan_repo: ContentPlanRepository = AsyncMock(spec=ContentPlanRepository)  # type: ignore[assignment]
    content_repo: SlideContentRepository = AsyncMock(spec=SlideContentRepository)  # type: ignore[assignment]
    prompt_repo: SystemPromptRepository = AsyncMock(spec=SystemPromptRepository)  # type: ignore[assignment]
    llm: LLMAdapter = AsyncMock(spec=LLMAdapter)  # type: ignore[assignment]

    router = create_content_router(
        plan_repo=plan_repo,
        content_repo=content_repo,
        prompt_repo=prompt_repo,
        event_bus=event_bus,
        llm=llm,
    )
    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "domain": "content"}

    return app


app = create_app()
