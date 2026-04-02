"""Agent domain — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from domains.agent.api.router import create_agent_router
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
        title="Presenton — Agent Domain",
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

    from domains.agent.domain.repositories import (
        AgentRepository,
        AgentPipelineRepository,
        AgentRunRepository,
        RalphLoopRepository,
    )
    from domains.agent.domain.services import SubAgentExecutor
    from unittest.mock import AsyncMock  # TODO: replace with real repos + executor
    run_repo: AgentRunRepository = AsyncMock(spec=AgentRunRepository)  # type: ignore[assignment]
    pipeline_repo: AgentPipelineRepository = AsyncMock(spec=AgentPipelineRepository)  # type: ignore[assignment]
    agent_repo: AgentRepository = AsyncMock(spec=AgentRepository)  # type: ignore[assignment]
    ralph_repo: RalphLoopRepository = AsyncMock(spec=RalphLoopRepository)  # type: ignore[assignment]
    executor: SubAgentExecutor = AsyncMock(spec=SubAgentExecutor)  # type: ignore[assignment]

    router = create_agent_router(
        run_repo=run_repo,
        pipeline_repo=pipeline_repo,
        agent_repo=agent_repo,
        ralph_repo=ralph_repo,
        executor=executor,
        event_bus=event_bus,
    )
    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "domain": "agent"}

    return app


app = create_app()
