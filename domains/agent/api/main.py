"""Agent domain — FastAPI application entry point."""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from domains.agent.infrastructure.workspace import Workspace

from domains.agent.api.router import create_agent_router
from domains.agent.domain.defaults import DEFAULT_AGENTS
from domains.agent.infrastructure.llm_client import LLMClient
from shared.infrastructure.config import get_settings
from shared.infrastructure.database import DatabaseConfig, create_engine_from_config
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus

logger = logging.getLogger(__name__)


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
        AgentPipelineRepository,
        AgentRunRepository,
        RalphLoopRepository,
    )
    from domains.agent.domain.services import SubAgentExecutor
    from domains.agent.infrastructure.repositories import InMemoryAgentRepository
    from unittest.mock import AsyncMock  # TODO: replace with real repos + executor
    run_repo: AgentRunRepository = AsyncMock(spec=AgentRunRepository)  # type: ignore[assignment]
    pipeline_repo: AgentPipelineRepository = AsyncMock(spec=AgentPipelineRepository)  # type: ignore[assignment]
    agent_repo = InMemoryAgentRepository()
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

    # ------------------------------------------------------------------
    # LLM-powered endpoints
    # ------------------------------------------------------------------

    def _get_llm() -> LLMClient:
        return LLMClient(auth_base_url="http://auth:8070")

    @app.post("/api/v1/agents/chat")
    async def agent_chat(request: dict) -> dict:
        """Chat with an agent. Used for Stage 1 interview."""
        agent_name = request.get("agent", "InterviewAgent")
        messages = request.get("messages", [])

        # Resolve agent config
        agent = await agent_repo.get_by_name(agent_name)
        if agent:
            config = agent.config
        else:
            config = DEFAULT_AGENTS.get(agent_name)  # type: ignore[assignment]
            if config is None:
                raise HTTPException(404, f"Agent '{agent_name}' not found")

        llm = _get_llm()
        try:
            response = await llm.chat(
                provider=config.provider,
                model=config.model,
                system_prompt=config.system_prompt,
                messages=messages,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        except Exception as exc:
            logger.exception("LLM call failed for agent %s", agent_name)
            raise HTTPException(502, f"LLM call failed: {exc}") from exc

        return {"content": response.content, "model": response.model, "agent": agent_name}

    @app.post("/api/v1/agents/generate")
    async def generate_presentation(request: dict) -> dict:
        """Run the 10-stage pipeline to generate a full presentation."""
        from domains.agent.infrastructure.pipeline_engine import PipelineEngine, PipelineError

        conversation = request.get("messages", request.get("conversation", []))
        slide_count = request.get("slide_count", 10)
        presentation_id = request.get("presentation_id")

        # Support legacy "brief" field: wrap it as a conversation message
        if not conversation and request.get("brief"):
            conversation = [{"role": "user", "content": request["brief"]}]

        if not presentation_id:
            presentation_id = str(uuid.uuid4())

        ws = Workspace(presentation_id)
        ws.initialize()

        llm = _get_llm()
        engine = PipelineEngine(ws, llm)

        try:
            results = await engine.run_full_pipeline(
                conversation=conversation,
                slide_count=slide_count,
                mode=request.get("mode", "from_scratch"),
            )
        except PipelineError as exc:
            state = ws.load_state()
            raise HTTPException(
                422,
                {
                    "error": f"Pipeline halted at {exc.stage}",
                    "failed_gates": exc.failed_gates,
                    "pipeline_state": asdict(state) if state else {},
                },
            ) from exc
        except Exception as exc:
            logger.exception("Pipeline failed")
            raise HTTPException(502, f"Pipeline error: {exc}") from exc

        render = results.get("render_qa", {})
        package = results.get("package", {})
        state = ws.load_state()

        return {
            "presentation_id": presentation_id,
            "slides": render.get("slides", []),
            "slide_count": len(render.get("slides", [])),
            "pipeline_state": asdict(state) if state else {},
            "output_files": package.get("files", []),
        }

    # ------------------------------------------------------------------
    # Workspace endpoints
    # ------------------------------------------------------------------

    @app.post("/api/v1/agents/workspace")
    async def create_workspace():
        """Create a new presentation workspace."""
        pid = str(uuid.uuid4())
        ws = Workspace(pid)
        ws.initialize()
        state = ws.load_state()
        return {"presentation_id": pid, "state": asdict(state)}

    @app.get("/api/v1/agents/workspace/{presentation_id}")
    async def get_workspace_state(presentation_id: str):
        """Get current pipeline state."""
        ws = Workspace(presentation_id)
        state = ws.load_state()
        if state is None:
            raise HTTPException(404, "Workspace not found")
        return asdict(state)

    @app.get("/api/v1/agents/workspace/{presentation_id}/artifact/{filename:path}")
    async def get_artifact(presentation_id: str, filename: str):
        """Read an artifact from the workspace."""
        ws = Workspace(presentation_id)
        if filename.endswith(".json"):
            data = ws.read_json(filename)
            if data is None:
                raise HTTPException(404, f"Artifact not found: {filename}")
            return data
        else:
            text = ws.read_text(filename)
            if text is None:
                raise HTTPException(404, f"Artifact not found: {filename}")
            return {"content": text, "filename": filename}

    # ------------------------------------------------------------------

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "domain": "agent"}

    return app


app = create_app()
