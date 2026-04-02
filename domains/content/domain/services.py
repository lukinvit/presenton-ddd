"""Content domain services — LLM adapter protocol and content generation logic."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Protocol

from .entities import ContentPlan, SlideContent, SystemPrompt
from .value_objects import OutlineItem


class LLMAdapter(Protocol):
    """Interface to LLM providers. Implementation calls Auth domain for tokens."""

    async def generate(
        self, system_prompt: str, user_prompt: str, model: str = "default"
    ) -> str: ...

    async def generate_stream(
        self, system_prompt: str, user_prompt: str, model: str = "default"
    ) -> AsyncIterator[str]: ...


class ContentService:
    """Domain service for constructing content entities."""

    def create_plan(
        self,
        presentation_id: uuid.UUID,
        topic: str,
        items: list[OutlineItem],
    ) -> ContentPlan:
        plan = ContentPlan(
            id=uuid.uuid4(),
            presentation_id=presentation_id,
            topic=topic,
        )
        plan.replace_outline(items)
        return plan

    def create_slide_content(
        self,
        plan_id: uuid.UUID,
        slide_index: int,
        title: str,
        body: str,
        speaker_notes: str,
    ) -> SlideContent:
        return SlideContent(
            id=uuid.uuid4(),
            plan_id=plan_id,
            slide_index=slide_index,
            title=title,
            body=body,
            speaker_notes=speaker_notes,
        )

    def create_system_prompt(
        self,
        name: str,
        prompt_text: str,
        variables: list[str],
        is_default: bool = False,
    ) -> SystemPrompt:
        return SystemPrompt(
            id=uuid.uuid4(),
            name=name,
            prompt_text=prompt_text,
            variables=list(variables),
            is_default=is_default,
        )
