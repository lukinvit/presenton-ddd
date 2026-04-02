"""FastAPI router for the content domain."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from domains.content.api.schemas import (
    ContentPlanResponse,
    CreateSystemPromptRequest,
    GenerateOutlineRequest,
    OutlineItemResponse,
    ReviseContentRequest,
    SlideContentResponse,
    SystemPromptResponse,
    UpdateSystemPromptRequest,
)
from domains.content.application.commands import (
    CreateSystemPromptCommand,
    GenerateOutlineCommand,
    GenerateSlideContentCommand,
    ReviseContentCommand,
    UpdateSystemPromptCommand,
)
from domains.content.application.dto import ContentPlanDTO, SlideContentDTO, SystemPromptDTO
from domains.content.application.queries import (
    GetContentPlanQuery,
    ListSystemPromptsQuery,
)
from domains.content.domain.repositories import (
    ContentPlanRepository,
    SlideContentRepository,
    SystemPromptRepository,
)
from domains.content.domain.services import ContentService, LLMAdapter
from shared.domain.events import EventBus

# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _dto_to_plan_response(dto: ContentPlanDTO) -> ContentPlanResponse:
    return ContentPlanResponse(
        id=dto.id,
        presentation_id=dto.presentation_id,
        topic=dto.topic,
        created_at=dto.created_at,
        outline=[
            OutlineItemResponse(
                index=item.index,
                title=item.title,
                key_points=item.key_points,
                suggested_layout=item.suggested_layout,
            )
            for item in dto.outline
        ],
    )


def _dto_to_slide_response(dto: SlideContentDTO) -> SlideContentResponse:
    return SlideContentResponse(
        id=dto.id,
        plan_id=dto.plan_id,
        slide_index=dto.slide_index,
        title=dto.title,
        body=dto.body,
        speaker_notes=dto.speaker_notes,
        generated_at=dto.generated_at,
    )


def _dto_to_prompt_response(dto: SystemPromptDTO) -> SystemPromptResponse:
    return SystemPromptResponse(
        id=dto.id,
        name=dto.name,
        prompt_text=dto.prompt_text,
        variables=dto.variables,
        is_default=dto.is_default,
        updated_at=dto.updated_at,
    )


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------


def create_content_router(
    plan_repo: ContentPlanRepository,
    content_repo: SlideContentRepository,
    prompt_repo: SystemPromptRepository,
    event_bus: EventBus,
    llm: LLMAdapter,
) -> APIRouter:
    router = APIRouter(tags=["content"])
    service = ContentService()

    # ------------------------------------------------------------------
    # Content generation
    # ------------------------------------------------------------------

    @router.post("/content/outline", response_model=ContentPlanResponse, status_code=201)
    async def generate_outline(req: GenerateOutlineRequest) -> ContentPlanResponse:
        cmd = GenerateOutlineCommand(
            plan_repo=plan_repo,
            event_bus=event_bus,
            llm=llm,
            service=service,
        )
        presentation_id = uuid.UUID(req.presentation_id) if req.presentation_id else None
        try:
            result = await cmd.execute(
                topic=req.topic,
                num_slides=req.num_slides,
                tone=req.tone,
                language=req.language,
                presentation_id=presentation_id,
            )
        except (ValueError, Exception) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _dto_to_plan_response(result)

    @router.post(
        "/content/slides/{plan_id}/{slide_index}",
        response_model=SlideContentResponse,
        status_code=201,
    )
    async def generate_slide(plan_id: uuid.UUID, slide_index: int) -> SlideContentResponse:
        cmd = GenerateSlideContentCommand(
            plan_repo=plan_repo,
            content_repo=content_repo,
            event_bus=event_bus,
            llm=llm,
            service=service,
        )
        try:
            result = await cmd.execute(plan_id=plan_id, slide_index=slide_index)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _dto_to_slide_response(result)

    @router.post(
        "/content/revise/{content_id}",
        response_model=SlideContentResponse,
    )
    async def revise_content(
        content_id: uuid.UUID, req: ReviseContentRequest
    ) -> SlideContentResponse:
        cmd = ReviseContentCommand(
            content_repo=content_repo,
            event_bus=event_bus,
            llm=llm,
        )
        try:
            result = await cmd.execute(slide_content_id=content_id, feedback=req.feedback)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _dto_to_slide_response(result)

    # ------------------------------------------------------------------
    # Plans
    # ------------------------------------------------------------------

    @router.get("/content/plans/{plan_id}", response_model=ContentPlanResponse)
    async def get_plan(plan_id: uuid.UUID) -> ContentPlanResponse:
        query = GetContentPlanQuery(plan_repo=plan_repo)
        try:
            result = await query.execute(plan_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _dto_to_plan_response(result)

    # ------------------------------------------------------------------
    # System prompts
    # ------------------------------------------------------------------

    @router.get("/content/prompts", response_model=list[SystemPromptResponse])
    async def list_prompts() -> list[SystemPromptResponse]:
        query = ListSystemPromptsQuery(prompt_repo=prompt_repo)
        results = await query.execute()
        return [_dto_to_prompt_response(r) for r in results]

    @router.post("/content/prompts", response_model=SystemPromptResponse, status_code=201)
    async def create_prompt(req: CreateSystemPromptRequest) -> SystemPromptResponse:
        cmd = CreateSystemPromptCommand(
            prompt_repo=prompt_repo,
            event_bus=event_bus,
            service=service,
        )
        try:
            result = await cmd.execute(
                name=req.name,
                prompt_text=req.prompt_text,
                variables=req.variables,
                is_default=req.is_default,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _dto_to_prompt_response(result)

    @router.put("/content/prompts/{prompt_id}", response_model=SystemPromptResponse)
    async def update_prompt(
        prompt_id: uuid.UUID, req: UpdateSystemPromptRequest
    ) -> SystemPromptResponse:
        cmd = UpdateSystemPromptCommand(
            prompt_repo=prompt_repo,
            event_bus=event_bus,
        )
        try:
            result = await cmd.execute(
                id=prompt_id,
                prompt_text=req.prompt_text,
                variables=req.variables,
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _dto_to_prompt_response(result)

    return router
