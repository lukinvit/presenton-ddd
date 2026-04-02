"""Rendering application queries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from domains.rendering.application.commands import _render_job_to_dto, _rendered_slide_to_dto
from domains.rendering.application.dto import RenderedSlideDTO, RenderJobDTO
from domains.rendering.domain.repositories import RenderJobRepository


@dataclass
class GetRenderJobQuery:
    repo: RenderJobRepository

    async def execute(self, job_id: uuid.UUID) -> RenderJobDTO:
        job = await self.repo.get(job_id)
        if job is None:
            raise ValueError(f"RenderJob '{job_id}' not found")
        return _render_job_to_dto(job)


@dataclass
class GetRenderedSlideQuery:
    repo: RenderJobRepository

    async def execute(self, slide_id: uuid.UUID) -> RenderedSlideDTO:
        """Find a rendered slide across all jobs by its slide_id."""
        jobs = await self.repo.list_all(limit=1000)
        for job in jobs:
            rendered = job.get_rendered_slide(slide_id)
            if rendered is not None:
                return _rendered_slide_to_dto(rendered)
        raise ValueError(f"RenderedSlide for slide '{slide_id}' not found")
