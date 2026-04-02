"""Content application commands."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from domains.content.application.dto import (
    ContentPlanDTO,
    OutlineItemDTO,
    SlideContentDTO,
    SystemPromptDTO,
)
from domains.content.domain.entities import ContentPlan, SlideContent, SystemPrompt
from domains.content.domain.events import (
    EVENT_CONTENT_REVISED,
    EVENT_OUTLINE_GENERATED,
    EVENT_SLIDE_CONTENT_GENERATED,
    EVENT_SYSTEM_PROMPT_CREATED,
    EVENT_SYSTEM_PROMPT_UPDATED,
)
from domains.content.domain.repositories import (
    ContentPlanRepository,
    SlideContentRepository,
    SystemPromptRepository,
)
from domains.content.domain.services import ContentService, LLMAdapter
from domains.content.domain.value_objects import OutlineItem
from shared.domain.events import DomainEvent, EventBus

# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------

_DEFAULT_OUTLINE_SYSTEM_PROMPT = (
    "You are a presentation expert. "
    "Generate a structured presentation outline as a JSON array. "
    "Each element must have: index (int, 0-based), title (str), "
    "key_points (list[str]), suggested_layout (str). "
    "Return ONLY valid JSON — no markdown, no extra text."
)

_DEFAULT_SLIDE_SYSTEM_PROMPT = (
    "You are a professional presentation writer. "
    "Given an outline item, write the slide content as a JSON object with fields: "
    "title (str), body (str), speaker_notes (str). "
    "Return ONLY valid JSON."
)

_DEFAULT_REVISE_SYSTEM_PROMPT = (
    "You are a professional presentation editor. "
    "Revise the given slide content based on the feedback provided. "
    "Return a JSON object with fields: title (str), body (str), speaker_notes (str). "
    "Return ONLY valid JSON."
)


def _plan_to_dto(plan: ContentPlan) -> ContentPlanDTO:
    return ContentPlanDTO(
        id=str(plan.id),
        presentation_id=str(plan.presentation_id),
        topic=plan.topic,
        created_at=plan.created_at.isoformat(),
        outline=[
            OutlineItemDTO(
                index=item.index,
                title=item.title,
                key_points=list(item.key_points),
                suggested_layout=item.suggested_layout,
            )
            for item in plan.outline
        ],
    )


def _slide_content_to_dto(sc: SlideContent) -> SlideContentDTO:
    return SlideContentDTO(
        id=str(sc.id),
        plan_id=str(sc.plan_id),
        slide_index=sc.slide_index,
        title=sc.title,
        body=sc.body,
        speaker_notes=sc.speaker_notes,
        generated_at=sc.generated_at.isoformat(),
    )


def _system_prompt_to_dto(sp: SystemPrompt) -> SystemPromptDTO:
    return SystemPromptDTO(
        id=str(sp.id),
        name=sp.name,
        prompt_text=sp.prompt_text,
        variables=list(sp.variables),
        is_default=sp.is_default,
        updated_at=sp.updated_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@dataclass
class GenerateOutlineCommand:
    plan_repo: ContentPlanRepository
    event_bus: EventBus
    llm: LLMAdapter
    service: ContentService | None = None

    def __post_init__(self) -> None:
        if self.service is None:
            self.service = ContentService()

    async def execute(
        self,
        topic: str,
        num_slides: int,
        tone: str = "professional",
        language: str = "English",
        presentation_id: uuid.UUID | None = None,
    ) -> ContentPlanDTO:
        if presentation_id is None:
            presentation_id = uuid.uuid4()

        user_prompt = (
            f"Create a {num_slides}-slide presentation outline about: {topic}. "
            f"Tone: {tone}. Language: {language}."
        )

        raw = await self.llm.generate(
            system_prompt=_DEFAULT_OUTLINE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        items_data: list[dict] = json.loads(raw)
        outline_items = [
            OutlineItem(
                index=item["index"],
                title=item["title"],
                key_points=tuple(item.get("key_points", [])),
                suggested_layout=item.get("suggested_layout", "content"),
            )
            for item in items_data
        ]

        plan = self.service.create_plan(  # type: ignore[union-attr]
            presentation_id=presentation_id,
            topic=topic,
            items=outline_items,
        )
        await self.plan_repo.save(plan)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=plan.id,
                event_type=EVENT_OUTLINE_GENERATED,
                payload={"plan_id": str(plan.id), "topic": topic},
            )
        )
        return _plan_to_dto(plan)


@dataclass
class GenerateSlideContentCommand:
    plan_repo: ContentPlanRepository
    content_repo: SlideContentRepository
    event_bus: EventBus
    llm: LLMAdapter
    service: ContentService | None = None

    def __post_init__(self) -> None:
        if self.service is None:
            self.service = ContentService()

    async def execute(self, plan_id: uuid.UUID, slide_index: int) -> SlideContentDTO:
        plan = await self.plan_repo.get(plan_id)
        if plan is None:
            raise ValueError(f"ContentPlan '{plan_id}' not found")

        matching = [item for item in plan.outline if item.index == slide_index]
        if not matching:
            raise ValueError(f"Slide index {slide_index} not found in plan '{plan_id}'")
        outline_item = matching[0]

        user_prompt = (
            f"Slide title: {outline_item.title}\n"
            f"Key points: {', '.join(outline_item.key_points)}\n"
            f"Layout: {outline_item.suggested_layout}"
        )

        raw = await self.llm.generate(
            system_prompt=_DEFAULT_SLIDE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        data = json.loads(raw)

        sc = self.service.create_slide_content(  # type: ignore[union-attr]
            plan_id=plan_id,
            slide_index=slide_index,
            title=data.get("title", outline_item.title),
            body=data.get("body", ""),
            speaker_notes=data.get("speaker_notes", ""),
        )
        await self.content_repo.save(sc)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=sc.id,
                event_type=EVENT_SLIDE_CONTENT_GENERATED,
                payload={"content_id": str(sc.id), "plan_id": str(plan_id)},
            )
        )
        return _slide_content_to_dto(sc)


@dataclass
class ReviseContentCommand:
    content_repo: SlideContentRepository
    event_bus: EventBus
    llm: LLMAdapter

    async def execute(self, slide_content_id: uuid.UUID, feedback: str) -> SlideContentDTO:
        sc = await self.content_repo.get(slide_content_id)
        if sc is None:
            raise ValueError(f"SlideContent '{slide_content_id}' not found")

        user_prompt = (
            f"Current title: {sc.title}\n"
            f"Current body: {sc.body}\n"
            f"Current speaker notes: {sc.speaker_notes}\n"
            f"Feedback: {feedback}"
        )

        raw = await self.llm.generate(
            system_prompt=_DEFAULT_REVISE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        data = json.loads(raw)

        sc.title = data.get("title", sc.title)
        sc.body = data.get("body", sc.body)
        sc.speaker_notes = data.get("speaker_notes", sc.speaker_notes)

        from datetime import UTC, datetime

        sc.generated_at = datetime.now(UTC)

        await self.content_repo.save(sc)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=sc.id,
                event_type=EVENT_CONTENT_REVISED,
                payload={"content_id": str(sc.id)},
            )
        )
        return _slide_content_to_dto(sc)


@dataclass
class CreateSystemPromptCommand:
    prompt_repo: SystemPromptRepository
    event_bus: EventBus
    service: ContentService | None = None

    def __post_init__(self) -> None:
        if self.service is None:
            self.service = ContentService()

    async def execute(
        self,
        name: str,
        prompt_text: str,
        variables: list[str],
        is_default: bool = False,
    ) -> SystemPromptDTO:
        sp = self.service.create_system_prompt(  # type: ignore[union-attr]
            name=name,
            prompt_text=prompt_text,
            variables=variables,
            is_default=is_default,
        )
        await self.prompt_repo.save(sp)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=sp.id,
                event_type=EVENT_SYSTEM_PROMPT_CREATED,
                payload={"prompt_id": str(sp.id), "name": name},
            )
        )
        return _system_prompt_to_dto(sp)


@dataclass
class UpdateSystemPromptCommand:
    prompt_repo: SystemPromptRepository
    event_bus: EventBus

    async def execute(
        self,
        id: uuid.UUID,
        prompt_text: str | None = None,
        variables: list[str] | None = None,
    ) -> SystemPromptDTO:
        sp = await self.prompt_repo.get(id)
        if sp is None:
            raise ValueError(f"SystemPrompt '{id}' not found")

        if prompt_text is not None:
            sp.update_text(prompt_text)
        if variables is not None:
            sp.update_variables(variables)

        await self.prompt_repo.save(sp)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=sp.id,
                event_type=EVENT_SYSTEM_PROMPT_UPDATED,
                payload={"prompt_id": str(sp.id)},
            )
        )
        return _system_prompt_to_dto(sp)
