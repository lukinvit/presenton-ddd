"""Unit tests for presentation application commands."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from domains.presentation.application.commands import (
    AddSlideCommand,
    CreatePresentationCommand,
    RemoveSlideCommand,
    ReorderSlidesCommand,
    UpdatePresentationCommand,
    UpdateSlideCommand,
)
from domains.presentation.application.dto import PresentationDTO, SlideDTO
from domains.presentation.domain.entities import Presentation, Slide


def _make_repo(presentation: Presentation | None = None) -> AsyncMock:
    repo = AsyncMock()
    repo.get = AsyncMock(return_value=presentation)
    repo.save = AsyncMock()
    repo.delete = AsyncMock()
    repo.list_all = AsyncMock(return_value=[])
    return repo


def _make_event_bus() -> AsyncMock:
    bus = AsyncMock()
    bus.publish = AsyncMock()
    return bus


class TestCreatePresentationCommand:
    async def test_creates_presentation(self) -> None:
        repo = _make_repo()
        bus = _make_event_bus()
        cmd = CreatePresentationCommand(repo=repo, event_bus=bus)
        result = await cmd.execute(title="My Deck", description="About stuff")

        assert isinstance(result, PresentationDTO)
        assert result.title == "My Deck"
        assert result.status == "draft"
        repo.save.assert_awaited_once()
        bus.publish.assert_awaited_once()

    async def test_publishes_created_event(self) -> None:
        repo = _make_repo()
        bus = _make_event_bus()
        cmd = CreatePresentationCommand(repo=repo, event_bus=bus)
        await cmd.execute(title="Deck")

        call_args = bus.publish.call_args[0][0]
        assert call_args.event_type == "PresentationCreated"


class TestUpdatePresentationCommand:
    async def test_updates_title(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Old", description="")
        repo = _make_repo(p)
        bus = _make_event_bus()
        cmd = UpdatePresentationCommand(repo=repo, event_bus=bus)
        result = await cmd.execute(presentation_id=p.id, title="New")
        assert result.title == "New"
        repo.save.assert_awaited_once()

    async def test_raises_if_not_found(self) -> None:
        repo = _make_repo(None)
        bus = _make_event_bus()
        cmd = UpdatePresentationCommand(repo=repo, event_bus=bus)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(presentation_id=uuid.uuid4())

    async def test_updates_status(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        repo = _make_repo(p)
        bus = _make_event_bus()
        cmd = UpdatePresentationCommand(repo=repo, event_bus=bus)
        result = await cmd.execute(presentation_id=p.id, status="review")
        assert result.status == "review"


class TestAddSlideCommand:
    async def test_adds_slide(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        repo = _make_repo(p)
        bus = _make_event_bus()
        cmd = AddSlideCommand(repo=repo, event_bus=bus)
        result = await cmd.execute(presentation_id=p.id, title="Intro")

        assert isinstance(result, SlideDTO)
        assert result.title == "Intro"
        assert result.index == 0
        assert len(p.slides) == 1
        bus.publish.assert_awaited_once()

    async def test_raises_if_presentation_not_found(self) -> None:
        repo = _make_repo(None)
        bus = _make_event_bus()
        cmd = AddSlideCommand(repo=repo, event_bus=bus)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(presentation_id=uuid.uuid4(), title="Slide")

    async def test_add_slide_at_index(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        s0 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S0")
        p.add_slide(s0)
        repo = _make_repo(p)
        bus = _make_event_bus()
        cmd = AddSlideCommand(repo=repo, event_bus=bus)
        await cmd.execute(presentation_id=p.id, title="New", index=0)
        assert p.slides[0].title == "New"
        assert p.slides[0].index == 0


class TestUpdateSlideCommand:
    async def test_updates_slide_title(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        s = Slide(id=uuid.uuid4(), presentation_id=p.id, title="Old")
        p.add_slide(s)
        repo = _make_repo(p)
        bus = _make_event_bus()
        cmd = UpdateSlideCommand(repo=repo, event_bus=bus)
        result = await cmd.execute(presentation_id=p.id, slide_id=s.id, title="New")
        assert result.title == "New"

    async def test_raises_if_slide_not_found(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        repo = _make_repo(p)
        bus = _make_event_bus()
        cmd = UpdateSlideCommand(repo=repo, event_bus=bus)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(presentation_id=p.id, slide_id=uuid.uuid4())

    async def test_updates_elements(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        s = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S")
        p.add_slide(s)
        repo = _make_repo(p)
        bus = _make_event_bus()
        cmd = UpdateSlideCommand(repo=repo, event_bus=bus)
        result = await cmd.execute(
            presentation_id=p.id,
            slide_id=s.id,
            elements=[{"type": "text", "content": "Hello", "position": {}, "style": {}}],
        )
        assert len(result.elements) == 1
        assert result.elements[0].content == "Hello"


class TestRemoveSlideCommand:
    async def test_removes_slide(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        s = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S")
        p.add_slide(s)
        repo = _make_repo(p)
        bus = _make_event_bus()
        cmd = RemoveSlideCommand(repo=repo, event_bus=bus)
        await cmd.execute(presentation_id=p.id, slide_id=s.id)
        assert len(p.slides) == 0
        bus.publish.assert_awaited_once()

    async def test_raises_if_slide_not_found(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        repo = _make_repo(p)
        bus = _make_event_bus()
        cmd = RemoveSlideCommand(repo=repo, event_bus=bus)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(presentation_id=p.id, slide_id=uuid.uuid4())


class TestReorderSlidesCommand:
    async def test_reorders_slides(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        s1 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S1")
        s2 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S2")
        s3 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S3")
        p.add_slide(s1)
        p.add_slide(s2)
        p.add_slide(s3)
        repo = _make_repo(p)
        bus = _make_event_bus()
        cmd = ReorderSlidesCommand(repo=repo, event_bus=bus)
        await cmd.execute(presentation_id=p.id, slide_ids=[s3.id, s2.id, s1.id])
        assert p.slides[0].title == "S3"
        assert p.slides[2].title == "S1"

    async def test_raises_on_mismatched_slide_ids(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        s1 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S1")
        p.add_slide(s1)
        repo = _make_repo(p)
        bus = _make_event_bus()
        cmd = ReorderSlidesCommand(repo=repo, event_bus=bus)
        with pytest.raises(ValueError, match="exactly the slides"):
            await cmd.execute(presentation_id=p.id, slide_ids=[uuid.uuid4()])
