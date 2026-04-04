"""Agent domain — FastAPI application entry point."""

from __future__ import annotations

import json
import logging
import re
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
        """Run a simplified production pipeline: ContentWriter -> SlideAssembler."""
        brief = request.get("brief", "")
        style_guide = request.get("style_guide", "")
        slide_count = request.get("slide_count", 10)

        llm = _get_llm()

        # --- Step 1: ContentWriter generates slide content ---
        content_config = DEFAULT_AGENTS["ContentWriter"]
        content_prompt = (
            f"Based on this creative brief, generate content for {slide_count} slides.\n\n"
            f"BRIEF:\n{brief}\n\n"
            f"STYLE GUIDE:\n{style_guide}\n\n"
            "Output JSON array with one object per slide:\n"
            "[\n"
            '  {{\n'
            '    "index": 0,\n'
            '    "title": "Slide Title",\n'
            '    "body": "Content text with bullet points",\n'
            '    "speaker_notes": "What to say",\n'
            '    "layout_type": "title_slide|content|two_column|image_full|data_chart|quote|section_divider",\n'
            '    "image_needs": "description of needed image or empty string"\n'
            "  }}\n"
            "]\n"
        )

        try:
            content_response = await llm.chat(
                provider=content_config.provider,
                model=content_config.model,
                system_prompt=content_config.system_prompt,
                messages=[{"role": "user", "content": content_prompt}],
                temperature=content_config.temperature,
                max_tokens=content_config.max_tokens * 2,
            )
        except Exception as exc:
            logger.exception("ContentWriter LLM call failed")
            raise HTTPException(502, f"ContentWriter failed: {exc}") from exc

        # Parse slides JSON
        slides_data = LLMClient.extract_json_array(content_response.content)
        if not slides_data:
            slides_data = [
                {
                    "index": 0,
                    "title": "Generated Presentation",
                    "body": content_response.content,
                    "layout_type": "content",
                }
            ]

        # --- Step 2: SlideAssembler generates HTML per slide ---
        assembler_config = DEFAULT_AGENTS["SlideAssembler"]
        html_slides: list[dict] = []

        for slide in slides_data:
            html_prompt = (
                "Create a complete HTML slide (1920x1080) for this content.\n\n"
                f"SLIDE DATA:\n{json.dumps(slide)}\n\n"
                f"STYLE GUIDE:\n{style_guide}\n\n"
                "Requirements:\n"
                "- Self-contained HTML with inline CSS\n"
                "- 1920x1080 viewport\n"
                "- Use the color palette and typography from the style guide\n"
                "- Clean, professional design\n"
                "- Include all content from the slide data\n\n"
                'Output ONLY the HTML (no markdown, no explanation). Start with <div class="slide"> and end with </div>.\n'
            )

            try:
                html_response = await llm.chat(
                    provider=assembler_config.provider,
                    model=assembler_config.model,
                    system_prompt=assembler_config.system_prompt,
                    messages=[{"role": "user", "content": html_prompt}],
                    temperature=assembler_config.temperature,
                    max_tokens=assembler_config.max_tokens,
                )
            except Exception as exc:
                logger.warning("SlideAssembler failed for slide %s: %s", slide.get("index"), exc)
                html_response_content = f'<div class="slide"><h1>{slide.get("title", "Slide")}</h1><p>{slide.get("body", "")}</p></div>'
                html_slides.append(
                    {
                        "index": slide.get("index", len(html_slides)),
                        "title": slide.get("title", f"Slide {len(html_slides) + 1}"),
                        "html": html_response_content,
                        "speaker_notes": slide.get("speaker_notes", ""),
                    }
                )
                continue

            # Strip markdown fences if present
            html_text = html_response.content
            html_text = re.sub(r"^```html?\s*", "", html_text, flags=re.MULTILINE)
            html_text = re.sub(r"```\s*$", "", html_text, flags=re.MULTILINE)

            html_slides.append(
                {
                    "index": slide.get("index", len(html_slides)),
                    "title": slide.get("title", f"Slide {len(html_slides) + 1}"),
                    "html": html_text.strip(),
                    "speaker_notes": slide.get("speaker_notes", ""),
                }
            )

        return {"slides": html_slides, "slide_count": len(html_slides)}

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
