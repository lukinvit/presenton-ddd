"""Unit tests for content application commands."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock

import pytest

from domains.content.application.commands import (
    CreateSystemPromptCommand,
    GenerateOutlineCommand,
    GenerateSlideContentCommand,
    ReviseContentCommand,
    UpdateSystemPromptCommand,
)
from domains.content.application.dto import ContentPlanDTO, SlideContentDTO, SystemPromptDTO
from domains.content.domain.entities import ContentPlan, SlideContent, SystemPrompt
from domains.content.domain.value_objects import OutlineItem

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_OUTLINE_JSON = json.dumps(
    [
        {
            "index": 0,
            "title": "Introduction",
            "key_points": ["What is AI?", "Why it matters"],
            "suggested_layout": "title",
        },
        {
            "index": 1,
            "title": "History",
            "key_points": ["Early days", "Deep learning era"],
            "suggested_layout": "content",
        },
    ]
)

_SLIDE_JSON = json.dumps(
    {
        "title": "Introduction",
        "body": "AI is transforming every industry.",
        "speaker_notes": "Start with a question to engage the audience.",
    }
)

_REVISE_JSON = json.dumps(
    {
        "title": "Revised Introduction",
        "body": "AI is reshaping industries worldwide.",
        "speaker_notes": "Open with a memorable statistic.",
    }
)


def _make_llm(return_value: str = _OUTLINE_JSON) -> AsyncMock:
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=return_value)
    return llm


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


def _make_prompt_repo(sp: SystemPrompt | None = None) -> AsyncMock:
    repo = AsyncMock()
    repo.get = AsyncMock(return_value=sp)
    repo.save = AsyncMock()
    repo.list_all = AsyncMock(return_value=[])
    return repo


def _make_event_bus() -> AsyncMock:
    bus = AsyncMock()
    bus.publish = AsyncMock()
    return bus


# ---------------------------------------------------------------------------
# GenerateOutlineCommand
# ---------------------------------------------------------------------------


class TestGenerateOutlineCommand:
    async def test_generates_outline(self) -> None:
        plan_repo = _make_plan_repo()
        bus = _make_event_bus()
        llm = _make_llm(_OUTLINE_JSON)

        cmd = GenerateOutlineCommand(plan_repo=plan_repo, event_bus=bus, llm=llm)
        result = await cmd.execute(topic="Artificial Intelligence", num_slides=2)

        assert isinstance(result, ContentPlanDTO)
        assert result.topic == "Artificial Intelligence"
        assert len(result.outline) == 2
        assert result.outline[0].title == "Introduction"
        assert result.outline[1].title == "History"
        plan_repo.save.assert_awaited_once()
        bus.publish.assert_awaited_once()

    async def test_publishes_outline_generated_event(self) -> None:
        plan_repo = _make_plan_repo()
        bus = _make_event_bus()
        llm = _make_llm(_OUTLINE_JSON)

        cmd = GenerateOutlineCommand(plan_repo=plan_repo, event_bus=bus, llm=llm)
        await cmd.execute(topic="Machine Learning", num_slides=2)

        event = bus.publish.call_args[0][0]
        assert event.event_type == "OutlineGenerated"

    async def test_uses_provided_presentation_id(self) -> None:
        plan_repo = _make_plan_repo()
        bus = _make_event_bus()
        llm = _make_llm(_OUTLINE_JSON)
        pid = uuid.uuid4()

        cmd = GenerateOutlineCommand(plan_repo=plan_repo, event_bus=bus, llm=llm)
        result = await cmd.execute(topic="AI", num_slides=2, presentation_id=pid)

        assert result.presentation_id == str(pid)

    async def test_passes_tone_and_language_to_llm(self) -> None:
        plan_repo = _make_plan_repo()
        bus = _make_event_bus()
        llm = _make_llm(_OUTLINE_JSON)

        cmd = GenerateOutlineCommand(plan_repo=plan_repo, event_bus=bus, llm=llm)
        await cmd.execute(topic="AI", num_slides=2, tone="casual", language="Spanish")

        call_kwargs = llm.generate.call_args
        user_prompt = call_kwargs[1]["user_prompt"] if call_kwargs[1] else call_kwargs[0][1]
        assert "casual" in user_prompt
        assert "Spanish" in user_prompt

    async def test_outline_items_have_correct_key_points(self) -> None:
        plan_repo = _make_plan_repo()
        bus = _make_event_bus()
        llm = _make_llm(_OUTLINE_JSON)

        cmd = GenerateOutlineCommand(plan_repo=plan_repo, event_bus=bus, llm=llm)
        result = await cmd.execute(topic="AI", num_slides=2)

        assert result.outline[0].key_points == ["What is AI?", "Why it matters"]


# ---------------------------------------------------------------------------
# GenerateSlideContentCommand
# ---------------------------------------------------------------------------


class TestGenerateSlideContentCommand:
    def _make_plan_with_item(self) -> ContentPlan:
        plan = ContentPlan(id=uuid.uuid4(), presentation_id=uuid.uuid4(), topic="AI")
        item = OutlineItem(
            index=0,
            title="Introduction",
            key_points=("What is AI?",),
            suggested_layout="title",
        )
        plan.add_item(item)
        return plan

    async def test_generates_slide_content(self) -> None:
        plan = self._make_plan_with_item()
        plan_repo = _make_plan_repo(plan)
        content_repo = _make_content_repo()
        bus = _make_event_bus()
        llm = _make_llm(_SLIDE_JSON)

        cmd = GenerateSlideContentCommand(
            plan_repo=plan_repo,
            content_repo=content_repo,
            event_bus=bus,
            llm=llm,
        )
        result = await cmd.execute(plan_id=plan.id, slide_index=0)

        assert isinstance(result, SlideContentDTO)
        assert result.title == "Introduction"
        assert "AI" in result.body
        content_repo.save.assert_awaited_once()
        bus.publish.assert_awaited_once()

    async def test_raises_if_plan_not_found(self) -> None:
        plan_repo = _make_plan_repo(None)
        content_repo = _make_content_repo()
        bus = _make_event_bus()
        llm = _make_llm(_SLIDE_JSON)

        cmd = GenerateSlideContentCommand(
            plan_repo=plan_repo,
            content_repo=content_repo,
            event_bus=bus,
            llm=llm,
        )
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(plan_id=uuid.uuid4(), slide_index=0)

    async def test_raises_if_slide_index_not_in_plan(self) -> None:
        plan = self._make_plan_with_item()
        plan_repo = _make_plan_repo(plan)
        content_repo = _make_content_repo()
        bus = _make_event_bus()
        llm = _make_llm(_SLIDE_JSON)

        cmd = GenerateSlideContentCommand(
            plan_repo=plan_repo,
            content_repo=content_repo,
            event_bus=bus,
            llm=llm,
        )
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(plan_id=plan.id, slide_index=99)

    async def test_publishes_event(self) -> None:
        plan = self._make_plan_with_item()
        plan_repo = _make_plan_repo(plan)
        content_repo = _make_content_repo()
        bus = _make_event_bus()
        llm = _make_llm(_SLIDE_JSON)

        cmd = GenerateSlideContentCommand(
            plan_repo=plan_repo,
            content_repo=content_repo,
            event_bus=bus,
            llm=llm,
        )
        await cmd.execute(plan_id=plan.id, slide_index=0)
        event = bus.publish.call_args[0][0]
        assert event.event_type == "SlideContentGenerated"


# ---------------------------------------------------------------------------
# ReviseContentCommand
# ---------------------------------------------------------------------------


class TestReviseContentCommand:
    def _make_slide_content(self) -> SlideContent:
        return SlideContent(
            id=uuid.uuid4(),
            plan_id=uuid.uuid4(),
            slide_index=0,
            title="Intro",
            body="Original body",
            speaker_notes="Original notes",
        )

    async def test_revises_content(self) -> None:
        sc = self._make_slide_content()
        content_repo = _make_content_repo(sc)
        bus = _make_event_bus()
        llm = _make_llm(_REVISE_JSON)

        cmd = ReviseContentCommand(content_repo=content_repo, event_bus=bus, llm=llm)
        result = await cmd.execute(slide_content_id=sc.id, feedback="Make it more impactful")

        assert isinstance(result, SlideContentDTO)
        assert result.title == "Revised Introduction"
        content_repo.save.assert_awaited_once()
        bus.publish.assert_awaited_once()

    async def test_raises_if_not_found(self) -> None:
        content_repo = _make_content_repo(None)
        bus = _make_event_bus()
        llm = _make_llm(_REVISE_JSON)

        cmd = ReviseContentCommand(content_repo=content_repo, event_bus=bus, llm=llm)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(slide_content_id=uuid.uuid4(), feedback="feedback")

    async def test_publishes_revised_event(self) -> None:
        sc = self._make_slide_content()
        content_repo = _make_content_repo(sc)
        bus = _make_event_bus()
        llm = _make_llm(_REVISE_JSON)

        cmd = ReviseContentCommand(content_repo=content_repo, event_bus=bus, llm=llm)
        await cmd.execute(slide_content_id=sc.id, feedback="feedback")

        event = bus.publish.call_args[0][0]
        assert event.event_type == "ContentRevised"


# ---------------------------------------------------------------------------
# CreateSystemPromptCommand
# ---------------------------------------------------------------------------


class TestCreateSystemPromptCommand:
    async def test_creates_prompt(self) -> None:
        prompt_repo = _make_prompt_repo()
        bus = _make_event_bus()

        cmd = CreateSystemPromptCommand(prompt_repo=prompt_repo, event_bus=bus)
        result = await cmd.execute(
            name="outline_generator",
            prompt_text="Generate an outline for {topic}",
            variables=["topic"],
        )

        assert isinstance(result, SystemPromptDTO)
        assert result.name == "outline_generator"
        assert result.variables == ["topic"]
        prompt_repo.save.assert_awaited_once()
        bus.publish.assert_awaited_once()

    async def test_publishes_created_event(self) -> None:
        prompt_repo = _make_prompt_repo()
        bus = _make_event_bus()

        cmd = CreateSystemPromptCommand(prompt_repo=prompt_repo, event_bus=bus)
        await cmd.execute(name="test", prompt_text="text", variables=[])

        event = bus.publish.call_args[0][0]
        assert event.event_type == "SystemPromptCreated"


# ---------------------------------------------------------------------------
# UpdateSystemPromptCommand
# ---------------------------------------------------------------------------


class TestUpdateSystemPromptCommand:
    async def test_updates_prompt_text(self) -> None:
        sp = SystemPrompt(id=uuid.uuid4(), name="test", prompt_text="Old", variables=["a"])
        prompt_repo = _make_prompt_repo(sp)
        bus = _make_event_bus()

        cmd = UpdateSystemPromptCommand(prompt_repo=prompt_repo, event_bus=bus)
        result = await cmd.execute(id=sp.id, prompt_text="New text")

        assert result.prompt_text == "New text"
        prompt_repo.save.assert_awaited_once()

    async def test_updates_variables(self) -> None:
        sp = SystemPrompt(id=uuid.uuid4(), name="test", prompt_text="Text", variables=["a"])
        prompt_repo = _make_prompt_repo(sp)
        bus = _make_event_bus()

        cmd = UpdateSystemPromptCommand(prompt_repo=prompt_repo, event_bus=bus)
        result = await cmd.execute(id=sp.id, variables=["b", "c"])

        assert result.variables == ["b", "c"]

    async def test_raises_if_not_found(self) -> None:
        prompt_repo = _make_prompt_repo(None)
        bus = _make_event_bus()

        cmd = UpdateSystemPromptCommand(prompt_repo=prompt_repo, event_bus=bus)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(id=uuid.uuid4(), prompt_text="text")

    async def test_publishes_updated_event(self) -> None:
        sp = SystemPrompt(id=uuid.uuid4(), name="test", prompt_text="Text", variables=[])
        prompt_repo = _make_prompt_repo(sp)
        bus = _make_event_bus()

        cmd = UpdateSystemPromptCommand(prompt_repo=prompt_repo, event_bus=bus)
        await cmd.execute(id=sp.id, prompt_text="New text")

        event = bus.publish.call_args[0][0]
        assert event.event_type == "SystemPromptUpdated"
