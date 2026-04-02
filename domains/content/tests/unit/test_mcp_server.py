"""Unit tests for content MCP server tools."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock

from domains.content.domain.entities import ContentPlan, SlideContent, SystemPrompt
from domains.content.domain.value_objects import OutlineItem
from domains.content.mcp.server import create_content_mcp_server

_OUTLINE_JSON = json.dumps(
    [
        {
            "index": 0,
            "title": "Intro",
            "key_points": ["Point A"],
            "suggested_layout": "title",
        }
    ]
)
_SLIDE_JSON = json.dumps({"title": "Intro", "body": "Body text", "speaker_notes": "Notes here"})
_REVISE_JSON = json.dumps(
    {"title": "Better Intro", "body": "Better body", "speaker_notes": "Better notes"}
)


def _make_plan_repo(plan: ContentPlan | None = None) -> AsyncMock:
    repo = AsyncMock()
    repo.get = AsyncMock(return_value=plan)
    repo.save = AsyncMock()
    return repo


def _make_content_repo(sc: SlideContent | None = None) -> AsyncMock:
    repo = AsyncMock()
    repo.get = AsyncMock(return_value=sc)
    repo.save = AsyncMock()
    return repo


def _make_prompt_repo(prompts: list[SystemPrompt] | None = None) -> AsyncMock:
    repo = AsyncMock()
    repo.get = AsyncMock(return_value=None)
    repo.save = AsyncMock()
    repo.list_all = AsyncMock(return_value=prompts or [])
    return repo


def _make_event_bus() -> AsyncMock:
    bus = AsyncMock()
    bus.publish = AsyncMock()
    return bus


def _make_llm(return_value: str = _OUTLINE_JSON) -> AsyncMock:
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=return_value)
    return llm


class TestContentMCPServerTools:
    async def test_generate_outline_tool(self) -> None:
        plan_repo = _make_plan_repo()
        content_repo = _make_content_repo()
        prompt_repo = _make_prompt_repo()
        bus = _make_event_bus()
        llm = _make_llm(_OUTLINE_JSON)

        server = create_content_mcp_server(
            plan_repo=plan_repo,
            content_repo=content_repo,
            prompt_repo=prompt_repo,
            event_bus=bus,
            llm=llm,
        )

        tool_fn = server.registered_tools["content.generate_outline"]
        result = await tool_fn(topic="AI", num_slides=1)
        assert result["topic"] == "AI"
        assert len(result["outline"]) == 1
        assert result["outline"][0]["title"] == "Intro"

    async def test_generate_slide_tool(self) -> None:
        plan = ContentPlan(id=uuid.uuid4(), presentation_id=uuid.uuid4(), topic="AI")
        plan.add_item(
            OutlineItem(index=0, title="Intro", key_points=("Point A",), suggested_layout="title")
        )
        plan_repo = _make_plan_repo(plan)
        content_repo = _make_content_repo()
        prompt_repo = _make_prompt_repo()
        bus = _make_event_bus()
        llm = _make_llm(_SLIDE_JSON)

        server = create_content_mcp_server(
            plan_repo=plan_repo,
            content_repo=content_repo,
            prompt_repo=prompt_repo,
            event_bus=bus,
            llm=llm,
        )

        tool_fn = server.registered_tools["content.generate_slide"]
        result = await tool_fn(plan_id=str(plan.id), slide_index=0)
        assert result["title"] == "Intro"
        assert result["body"] == "Body text"

    async def test_revise_tool(self) -> None:
        sc = SlideContent(
            id=uuid.uuid4(),
            plan_id=uuid.uuid4(),
            slide_index=0,
            title="Intro",
            body="Old body",
            speaker_notes="Old notes",
        )
        content_repo = _make_content_repo(sc)
        plan_repo = _make_plan_repo()
        prompt_repo = _make_prompt_repo()
        bus = _make_event_bus()
        llm = _make_llm(_REVISE_JSON)

        server = create_content_mcp_server(
            plan_repo=plan_repo,
            content_repo=content_repo,
            prompt_repo=prompt_repo,
            event_bus=bus,
            llm=llm,
        )

        tool_fn = server.registered_tools["content.revise"]
        result = await tool_fn(content_id=str(sc.id), feedback="Make it better")
        assert result["title"] == "Better Intro"

    async def test_prompts_list_tool(self) -> None:
        sp = SystemPrompt(
            id=uuid.uuid4(),
            name="outline_generator",
            prompt_text="Generate outline for {topic}",
            variables=["topic"],
        )
        plan_repo = _make_plan_repo()
        content_repo = _make_content_repo()
        prompt_repo = _make_prompt_repo([sp])
        bus = _make_event_bus()
        llm = _make_llm()

        server = create_content_mcp_server(
            plan_repo=plan_repo,
            content_repo=content_repo,
            prompt_repo=prompt_repo,
            event_bus=bus,
            llm=llm,
        )

        tool_fn = server.registered_tools["content.prompts.list"]
        result = await tool_fn()
        assert len(result) == 1
        assert result[0]["name"] == "outline_generator"

    async def test_prompts_create_tool(self) -> None:
        plan_repo = _make_plan_repo()
        content_repo = _make_content_repo()
        prompt_repo = _make_prompt_repo()
        bus = _make_event_bus()
        llm = _make_llm()

        server = create_content_mcp_server(
            plan_repo=plan_repo,
            content_repo=content_repo,
            prompt_repo=prompt_repo,
            event_bus=bus,
            llm=llm,
        )

        tool_fn = server.registered_tools["content.prompts.create"]
        result = await tool_fn(
            name="slide_writer",
            prompt_text="Write slide content for {topic}",
            variables=["topic"],
        )
        assert result["name"] == "slide_writer"

    async def test_prompts_update_tool(self) -> None:
        sp = SystemPrompt(
            id=uuid.uuid4(),
            name="test",
            prompt_text="Old",
            variables=[],
        )
        plan_repo = _make_plan_repo()
        content_repo = _make_content_repo()
        prompt_repo = _make_prompt_repo()
        prompt_repo.get = AsyncMock(return_value=sp)
        bus = _make_event_bus()
        llm = _make_llm()

        server = create_content_mcp_server(
            plan_repo=plan_repo,
            content_repo=content_repo,
            prompt_repo=prompt_repo,
            event_bus=bus,
            llm=llm,
        )

        tool_fn = server.registered_tools["content.prompts.update"]
        result = await tool_fn(prompt_id=str(sp.id), prompt_text="New text")
        assert result["prompt_text"] == "New text"

    async def test_health_check_tool(self) -> None:
        plan_repo = _make_plan_repo()
        content_repo = _make_content_repo()
        prompt_repo = _make_prompt_repo()
        bus = _make_event_bus()
        llm = _make_llm()

        server = create_content_mcp_server(
            plan_repo=plan_repo,
            content_repo=content_repo,
            prompt_repo=prompt_repo,
            event_bus=bus,
            llm=llm,
        )

        tool_fn = server.registered_tools["health.check"]
        result = await tool_fn()
        assert result["status"] == "ok"
        assert result["domain"] == "content"
