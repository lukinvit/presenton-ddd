"""Content application queries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from domains.content.application.commands import (
    _plan_to_dto,
    _slide_content_to_dto,
    _system_prompt_to_dto,
)
from domains.content.application.dto import ContentPlanDTO, SlideContentDTO, SystemPromptDTO
from domains.content.domain.repositories import (
    ContentPlanRepository,
    SlideContentRepository,
    SystemPromptRepository,
)


@dataclass
class GetContentPlanQuery:
    plan_repo: ContentPlanRepository

    async def execute(self, plan_id: uuid.UUID) -> ContentPlanDTO:
        plan = await self.plan_repo.get(plan_id)
        if plan is None:
            raise ValueError(f"ContentPlan '{plan_id}' not found")
        return _plan_to_dto(plan)


@dataclass
class GetSlideContentQuery:
    content_repo: SlideContentRepository

    async def execute(self, content_id: uuid.UUID) -> SlideContentDTO:
        sc = await self.content_repo.get(content_id)
        if sc is None:
            raise ValueError(f"SlideContent '{content_id}' not found")
        return _slide_content_to_dto(sc)


@dataclass
class ListSystemPromptsQuery:
    prompt_repo: SystemPromptRepository

    async def execute(self) -> list[SystemPromptDTO]:
        prompts = await self.prompt_repo.list_all()
        return [_system_prompt_to_dto(p) for p in prompts]
