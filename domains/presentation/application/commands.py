"""Presentation application commands."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from domains.presentation.application.dto import PresentationDTO, SlideDTO, SlideElementDTO
from domains.presentation.domain.entities import Presentation, Slide
from domains.presentation.domain.events import (
    EVENT_PRESENTATION_CREATED,
    EVENT_PRESENTATION_UPDATED,
    EVENT_SLIDE_ADDED,
    EVENT_SLIDE_REMOVED,
    EVENT_SLIDE_UPDATED,
    EVENT_SLIDES_REORDERED,
)
from domains.presentation.domain.repositories import PresentationRepository
from domains.presentation.domain.services import PresentationService
from domains.presentation.domain.value_objects import ElementType, PresentationStatus, SlideElement
from shared.domain.events import DomainEvent, EventBus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slide_to_dto(slide: Slide) -> SlideDTO:
    return SlideDTO(
        id=str(slide.id),
        presentation_id=str(slide.presentation_id),
        index=slide.index,
        title=slide.title,
        layout_type=slide.layout_type,
        speaker_notes=slide.speaker_notes,
        elements=[
            SlideElementDTO(
                type=e.type.value,
                content=e.content,
                position=e.position,
                style=e.style,
            )
            for e in slide.elements
        ],
    )


def _presentation_to_dto(p: Presentation) -> PresentationDTO:
    return PresentationDTO(
        id=str(p.id),
        title=p.title,
        description=p.description,
        status=p.status.value,
        template_id=str(p.template_id) if p.template_id else None,
        style_profile_id=str(p.style_profile_id) if p.style_profile_id else None,
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
        slides=[_slide_to_dto(s) for s in p.slides],
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@dataclass
class CreatePresentationCommand:
    repo: PresentationRepository
    event_bus: EventBus
    service: PresentationService = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.service is None:
            self.service = PresentationService()

    async def execute(self, title: str, description: str = "") -> PresentationDTO:
        presentation = self.service.create_presentation(title=title, description=description)
        await self.repo.save(presentation)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=presentation.id,
                event_type=EVENT_PRESENTATION_CREATED,
                payload={"presentation_id": str(presentation.id), "title": presentation.title},
            )
        )
        return _presentation_to_dto(presentation)


@dataclass
class UpdatePresentationCommand:
    repo: PresentationRepository
    event_bus: EventBus

    async def execute(
        self,
        presentation_id: uuid.UUID,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> PresentationDTO:
        presentation = await self.repo.get(presentation_id)
        if presentation is None:
            raise ValueError(f"Presentation '{presentation_id}' not found")
        if title is not None:
            presentation.update_title(title)
        if description is not None:
            presentation.update_description(description)
        if status is not None:
            presentation.update_status(PresentationStatus(status))
        await self.repo.save(presentation)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=presentation.id,
                event_type=EVENT_PRESENTATION_UPDATED,
                payload={"presentation_id": str(presentation.id)},
            )
        )
        return _presentation_to_dto(presentation)


@dataclass
class AddSlideCommand:
    repo: PresentationRepository
    event_bus: EventBus
    service: PresentationService = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.service is None:
            self.service = PresentationService()

    async def execute(
        self,
        presentation_id: uuid.UUID,
        title: str,
        layout_type: str = "content",
        index: int | None = None,
        speaker_notes: str = "",
    ) -> SlideDTO:
        presentation = await self.repo.get(presentation_id)
        if presentation is None:
            raise ValueError(f"Presentation '{presentation_id}' not found")
        slide = self.service.create_slide(
            presentation_id=presentation_id,
            title=title,
            layout_type=layout_type,
            speaker_notes=speaker_notes,
        )
        if index is not None:
            presentation.insert_slide(slide, index)
        else:
            presentation.add_slide(slide)
        await self.repo.save(presentation)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=presentation.id,
                event_type=EVENT_SLIDE_ADDED,
                payload={
                    "presentation_id": str(presentation.id),
                    "slide_id": str(slide.id),
                },
            )
        )
        return _slide_to_dto(slide)


@dataclass
class UpdateSlideCommand:
    repo: PresentationRepository
    event_bus: EventBus

    async def execute(
        self,
        presentation_id: uuid.UUID,
        slide_id: uuid.UUID,
        title: str | None = None,
        elements: list[dict[str, Any]] | None = None,
        speaker_notes: str | None = None,
    ) -> SlideDTO:
        presentation = await self.repo.get(presentation_id)
        if presentation is None:
            raise ValueError(f"Presentation '{presentation_id}' not found")
        slide = presentation.get_slide(slide_id)
        if slide is None:
            raise ValueError(f"Slide '{slide_id}' not found in presentation")
        if title is not None:
            slide.title = title
        if speaker_notes is not None:
            slide.speaker_notes = speaker_notes
        if elements is not None:
            parsed = [
                SlideElement(
                    type=ElementType(e["type"]),
                    content=e["content"],
                    position=e.get("position", {}),
                    style=e.get("style", {}),
                )
                for e in elements
            ]
            slide.replace_elements(parsed)
        from datetime import UTC, datetime

        presentation.updated_at = datetime.now(UTC)
        await self.repo.save(presentation)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=presentation.id,
                event_type=EVENT_SLIDE_UPDATED,
                payload={
                    "presentation_id": str(presentation.id),
                    "slide_id": str(slide.id),
                },
            )
        )
        return _slide_to_dto(slide)


@dataclass
class RemoveSlideCommand:
    repo: PresentationRepository
    event_bus: EventBus

    async def execute(self, presentation_id: uuid.UUID, slide_id: uuid.UUID) -> None:
        presentation = await self.repo.get(presentation_id)
        if presentation is None:
            raise ValueError(f"Presentation '{presentation_id}' not found")
        if presentation.get_slide(slide_id) is None:
            raise ValueError(f"Slide '{slide_id}' not found in presentation")
        presentation.remove_slide(slide_id)
        await self.repo.save(presentation)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=presentation.id,
                event_type=EVENT_SLIDE_REMOVED,
                payload={
                    "presentation_id": str(presentation.id),
                    "slide_id": str(slide_id),
                },
            )
        )


@dataclass
class ReorderSlidesCommand:
    repo: PresentationRepository
    event_bus: EventBus
    service: PresentationService = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.service is None:
            self.service = PresentationService()

    async def execute(self, presentation_id: uuid.UUID, slide_ids: list[uuid.UUID]) -> None:
        presentation = await self.repo.get(presentation_id)
        if presentation is None:
            raise ValueError(f"Presentation '{presentation_id}' not found")
        self.service.validate_slide_order(presentation, slide_ids)
        presentation.reorder_slides(slide_ids)
        await self.repo.save(presentation)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=presentation.id,
                event_type=EVENT_SLIDES_REORDERED,
                payload={"presentation_id": str(presentation.id)},
            )
        )
