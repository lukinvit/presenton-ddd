"""FastAPI router for the rendering domain."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from domains.rendering.api.schemas import (
    BatchRenderRequest,
    RenderedSlideResponse,
    RenderJobResponse,
    RenderPresentationRequest,
    RenderSlideRequest,
    VisualDiffRequest,
    VisualDiffResponse,
)
from domains.rendering.application.commands import (
    BatchRenderCommand,
    ComputeVisualDiffCommand,
    RenderPresentationCommand,
    RenderSlideCommand,
)
from domains.rendering.application.dto import RenderedSlideDTO, RenderJobDTO, VisualDiffResultDTO
from domains.rendering.application.queries import GetRenderJobQuery
from domains.rendering.domain.repositories import RenderJobRepository
from domains.rendering.domain.services import HTMLRenderer, VisualDiffService
from domains.rendering.domain.value_objects import RenderConfig

# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _dto_to_rendered_slide_response(dto: RenderedSlideDTO) -> RenderedSlideResponse:
    return RenderedSlideResponse(
        id=dto.id,
        slide_id=dto.slide_id,
        html=dto.html,
        thumbnail_url=dto.thumbnail_url,
        render_time_ms=dto.render_time_ms,
    )


def _dto_to_render_job_response(dto: RenderJobDTO) -> RenderJobResponse:
    return RenderJobResponse(
        id=dto.id,
        presentation_id=dto.presentation_id,
        status=dto.status,
        config_width=dto.config_width,
        config_height=dto.config_height,
        config_format=dto.config_format,
        config_include_css=dto.config_include_css,
        created_at=dto.created_at,
        completed_at=dto.completed_at,
        rendered_slides=[_dto_to_rendered_slide_response(s) for s in dto.rendered_slides],
    )


def _dto_to_visual_diff_response(dto: VisualDiffResultDTO) -> VisualDiffResponse:
    return VisualDiffResponse(
        slide_id=dto.slide_id,
        difference_percent=dto.difference_percent,
        changed_regions=dto.changed_regions,
    )


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------


def create_rendering_router(
    repo: RenderJobRepository,
    html_renderer: HTMLRenderer,
    diff_service: VisualDiffService | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/rendering", tags=["rendering"])
    _diff_service = diff_service or VisualDiffService()

    @router.post("/slides", response_model=RenderedSlideResponse, status_code=201)
    async def render_slide(req: RenderSlideRequest) -> RenderedSlideResponse:
        config = RenderConfig(
            width=req.config.width,
            height=req.config.height,
            format=req.config.format,
            include_css=req.config.include_css,
        )
        cmd = RenderSlideCommand(html_renderer=html_renderer)
        try:
            result = await cmd.execute(
                slide_id=req.slide_id,
                slide_data=req.slide_data,
                css_variables=req.css_variables,
                config=config,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        return _dto_to_rendered_slide_response(result)

    @router.post(
        "/presentations/{presentation_id}",
        response_model=RenderJobResponse,
        status_code=201,
    )
    async def render_presentation(
        presentation_id: uuid.UUID, req: RenderPresentationRequest
    ) -> RenderJobResponse:
        config = RenderConfig(
            width=req.config.width,
            height=req.config.height,
            format=req.config.format,
            include_css=req.config.include_css,
        )
        slides_data: list[dict[str, Any]] = [
            {"slide_id": str(item.slide_id), "data": item.data} for item in req.slides_data
        ]
        cmd = RenderPresentationCommand(
            repo=repo,
            html_renderer=html_renderer,
            config=config,
        )
        try:
            result = await cmd.execute(
                presentation_id=presentation_id,
                slides_data=slides_data,
                css_variables=req.css_variables,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        return _dto_to_render_job_response(result)

    @router.post("/visual-diff", response_model=VisualDiffResponse)
    async def compute_visual_diff(req: VisualDiffRequest) -> VisualDiffResponse:
        cmd = ComputeVisualDiffCommand(diff_service=_diff_service)
        try:
            result = await cmd.execute(
                slide_id=req.slide_id,
                image_a=req.image_a,
                image_b=req.image_b,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        return _dto_to_visual_diff_response(result)

    @router.get("/jobs/{job_id}", response_model=RenderJobResponse)
    async def get_render_job(job_id: uuid.UUID) -> RenderJobResponse:
        query = GetRenderJobQuery(repo=repo)
        try:
            result = await query.execute(job_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _dto_to_render_job_response(result)

    @router.post("/jobs/{job_id}/batch", response_model=RenderJobResponse)
    async def batch_render(job_id: uuid.UUID, req: BatchRenderRequest) -> RenderJobResponse:
        slides_data: list[dict[str, Any]] = [
            {"slide_id": str(item.slide_id), "data": item.data} for item in req.slides_data
        ]
        cmd = BatchRenderCommand(
            repo=repo,
            html_renderer=html_renderer,
            slides_data=slides_data,
            css_variables=req.css_variables,
        )
        try:
            result = await cmd.execute(render_job_id=job_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        return _dto_to_render_job_response(result)

    return router
