"""MCP server for the content domain."""

from __future__ import annotations

import uuid

from domains.content.domain.repositories import (
    ContentPlanRepository,
    SlideContentRepository,
    SystemPromptRepository,
)
from domains.content.domain.services import ContentService, LLMAdapter
from shared.domain.events import EventBus
from shared.mcp.server_base import DomainMCPServer


def create_content_mcp_server(
    plan_repo: ContentPlanRepository,
    content_repo: SlideContentRepository,
    prompt_repo: SystemPromptRepository,
    event_bus: EventBus,
    llm: LLMAdapter,
) -> DomainMCPServer:
    server = DomainMCPServer(name="content", port=9084)
    service = ContentService()

    # ------------------------------------------------------------------
    # Content generation tools
    # ------------------------------------------------------------------

    @server.tool("content.generate_outline")
    async def content_generate_outline(
        topic: str,
        num_slides: int = 5,
        tone: str = "professional",
        language: str = "English",
        presentation_id: str | None = None,
    ) -> dict:
        from domains.content.application.commands import GenerateOutlineCommand

        cmd = GenerateOutlineCommand(
            plan_repo=plan_repo,
            event_bus=event_bus,
            llm=llm,
            service=service,
        )
        pid = uuid.UUID(presentation_id) if presentation_id else None
        result = await cmd.execute(
            topic=topic,
            num_slides=num_slides,
            tone=tone,
            language=language,
            presentation_id=pid,
        )
        return {
            "id": result.id,
            "presentation_id": result.presentation_id,
            "topic": result.topic,
            "outline": [
                {
                    "index": item.index,
                    "title": item.title,
                    "key_points": item.key_points,
                    "suggested_layout": item.suggested_layout,
                }
                for item in result.outline
            ],
        }

    @server.tool("content.generate_slide")
    async def content_generate_slide(plan_id: str, slide_index: int) -> dict:
        from domains.content.application.commands import GenerateSlideContentCommand

        cmd = GenerateSlideContentCommand(
            plan_repo=plan_repo,
            content_repo=content_repo,
            event_bus=event_bus,
            llm=llm,
            service=service,
        )
        result = await cmd.execute(
            plan_id=uuid.UUID(plan_id),
            slide_index=slide_index,
        )
        return {
            "id": result.id,
            "plan_id": result.plan_id,
            "slide_index": result.slide_index,
            "title": result.title,
            "body": result.body,
            "speaker_notes": result.speaker_notes,
        }

    @server.tool("content.revise")
    async def content_revise(content_id: str, feedback: str) -> dict:
        from domains.content.application.commands import ReviseContentCommand

        cmd = ReviseContentCommand(
            content_repo=content_repo,
            event_bus=event_bus,
            llm=llm,
        )
        result = await cmd.execute(
            slide_content_id=uuid.UUID(content_id),
            feedback=feedback,
        )
        return {
            "id": result.id,
            "title": result.title,
            "body": result.body,
            "speaker_notes": result.speaker_notes,
        }

    # ------------------------------------------------------------------
    # System prompt tools
    # ------------------------------------------------------------------

    @server.tool("content.prompts.list")
    async def content_prompts_list() -> list[dict]:
        from domains.content.application.queries import ListSystemPromptsQuery

        query = ListSystemPromptsQuery(prompt_repo=prompt_repo)
        results = await query.execute()
        return [
            {
                "id": r.id,
                "name": r.name,
                "variables": r.variables,
                "is_default": r.is_default,
            }
            for r in results
        ]

    @server.tool("content.prompts.create")
    async def content_prompts_create(
        name: str,
        prompt_text: str,
        variables: list[str] | None = None,
        is_default: bool = False,
    ) -> dict:
        from domains.content.application.commands import CreateSystemPromptCommand

        cmd = CreateSystemPromptCommand(
            prompt_repo=prompt_repo,
            event_bus=event_bus,
            service=service,
        )
        result = await cmd.execute(
            name=name,
            prompt_text=prompt_text,
            variables=variables or [],
            is_default=is_default,
        )
        return {
            "id": result.id,
            "name": result.name,
            "variables": result.variables,
            "is_default": result.is_default,
        }

    @server.tool("content.prompts.update")
    async def content_prompts_update(
        prompt_id: str,
        prompt_text: str | None = None,
        variables: list[str] | None = None,
    ) -> dict:
        from domains.content.application.commands import UpdateSystemPromptCommand

        cmd = UpdateSystemPromptCommand(
            prompt_repo=prompt_repo,
            event_bus=event_bus,
        )
        result = await cmd.execute(
            id=uuid.UUID(prompt_id),
            prompt_text=prompt_text,
            variables=variables,
        )
        return {
            "id": result.id,
            "name": result.name,
            "prompt_text": result.prompt_text,
            "variables": result.variables,
        }

    return server
