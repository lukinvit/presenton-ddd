"""FastAPI router for the presentation domain."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from domains.presentation.api.schemas import (
    AddSlideRequest,
    CreatePresentationRequest,
    PresentationResponse,
    ReorderSlidesRequest,
    SlideElementResponse,
    SlideResponse,
    UpdatePresentationRequest,
    UpdateSlideRequest,
)
from domains.presentation.application.commands import (
    AddSlideCommand,
    CreatePresentationCommand,
    RemoveSlideCommand,
    ReorderSlidesCommand,
    UpdatePresentationCommand,
    UpdateSlideCommand,
)
from domains.presentation.application.dto import PresentationDTO, SlideDTO
from domains.presentation.application.queries import GetPresentationQuery, ListPresentationsQuery
from domains.presentation.domain.repositories import PresentationRepository
from domains.presentation.domain.services import PresentationService
from shared.domain.events import EventBus

# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _dto_to_slide_response(dto: SlideDTO) -> SlideResponse:
    return SlideResponse(
        id=dto.id,
        presentation_id=dto.presentation_id,
        index=dto.index,
        title=dto.title,
        layout_type=dto.layout_type,
        speaker_notes=dto.speaker_notes,
        elements=[
            SlideElementResponse(
                type=e.type,
                content=e.content,
                position=e.position,
                style=e.style,
            )
            for e in dto.elements
        ],
    )


def _dto_to_presentation_response(dto: PresentationDTO) -> PresentationResponse:
    return PresentationResponse(
        id=dto.id,
        title=dto.title,
        description=dto.description,
        status=dto.status,
        template_id=dto.template_id,
        style_profile_id=dto.style_profile_id,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
        slides=[_dto_to_slide_response(s) for s in dto.slides],
    )


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------


def create_presentation_router(
    repo: PresentationRepository,
    event_bus: EventBus,
) -> APIRouter:
    router = APIRouter(tags=["presentations"])
    service = PresentationService()

    # ------------------------------------------------------------------
    # Presentation CRUD
    # ------------------------------------------------------------------

    @router.post("/presentations", response_model=PresentationResponse, status_code=201)
    async def create_presentation(req: CreatePresentationRequest) -> PresentationResponse:
        cmd = CreatePresentationCommand(repo=repo, event_bus=event_bus, service=service)
        try:
            result = await cmd.execute(title=req.title, description=req.description)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _dto_to_presentation_response(result)

    @router.get("/presentations", response_model=list[PresentationResponse])
    async def list_presentations(limit: int = 50, offset: int = 0) -> list[PresentationResponse]:
        query = ListPresentationsQuery(repo=repo)
        results = await query.execute(limit=limit, offset=offset)
        return [_dto_to_presentation_response(r) for r in results]

    @router.get("/presentations/{presentation_id}", response_model=PresentationResponse)
    async def get_presentation(presentation_id: uuid.UUID) -> PresentationResponse:
        query = GetPresentationQuery(repo=repo)
        try:
            result = await query.execute(presentation_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _dto_to_presentation_response(result)

    @router.put("/presentations/{presentation_id}", response_model=PresentationResponse)
    async def update_presentation(
        presentation_id: uuid.UUID, req: UpdatePresentationRequest
    ) -> PresentationResponse:
        cmd = UpdatePresentationCommand(repo=repo, event_bus=event_bus)
        try:
            result = await cmd.execute(
                presentation_id=presentation_id,
                title=req.title,
                description=req.description,
                status=req.status,
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _dto_to_presentation_response(result)

    @router.delete("/presentations/{presentation_id}", status_code=204)
    async def delete_presentation(presentation_id: uuid.UUID) -> None:
        presentation = await repo.get(presentation_id)
        if presentation is None:
            raise HTTPException(
                status_code=404, detail=f"Presentation '{presentation_id}' not found"
            )
        await repo.delete(presentation_id)

    # ------------------------------------------------------------------
    # Slide management
    # ------------------------------------------------------------------

    @router.post(
        "/presentations/{presentation_id}/slides",
        response_model=SlideResponse,
        status_code=201,
    )
    async def add_slide(presentation_id: uuid.UUID, req: AddSlideRequest) -> SlideResponse:
        cmd = AddSlideCommand(repo=repo, event_bus=event_bus, service=service)
        try:
            result = await cmd.execute(
                presentation_id=presentation_id,
                title=req.title,
                layout_type=req.layout_type,
                index=req.index,
                speaker_notes=req.speaker_notes,
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _dto_to_slide_response(result)

    # NOTE: reorder must be defined BEFORE /{slide_id} routes to avoid being
    # captured as a dynamic path segment.
    @router.put(
        "/presentations/{presentation_id}/slides/reorder",
        status_code=200,
    )
    async def reorder_slides(
        presentation_id: uuid.UUID, req: ReorderSlidesRequest
    ) -> dict[str, str]:
        cmd = ReorderSlidesCommand(repo=repo, event_bus=event_bus, service=service)
        try:
            await cmd.execute(presentation_id=presentation_id, slide_ids=req.slide_ids)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return {"status": "ok"}

    @router.put(
        "/presentations/{presentation_id}/slides/{slide_id}",
        response_model=SlideResponse,
    )
    async def update_slide(
        presentation_id: uuid.UUID, slide_id: uuid.UUID, req: UpdateSlideRequest
    ) -> SlideResponse:
        cmd = UpdateSlideCommand(repo=repo, event_bus=event_bus)
        elements_data = None
        if req.elements is not None:
            elements_data = [e.model_dump() for e in req.elements]
        try:
            result = await cmd.execute(
                presentation_id=presentation_id,
                slide_id=slide_id,
                title=req.title,
                elements=elements_data,
                speaker_notes=req.speaker_notes,
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _dto_to_slide_response(result)

    @router.delete(
        "/presentations/{presentation_id}/slides/{slide_id}",
        status_code=204,
    )
    async def remove_slide(presentation_id: uuid.UUID, slide_id: uuid.UUID) -> None:
        cmd = RemoveSlideCommand(repo=repo, event_bus=event_bus)
        try:
            await cmd.execute(presentation_id=presentation_id, slide_id=slide_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

    return router
