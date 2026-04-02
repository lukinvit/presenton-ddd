"""Rendering application commands."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from domains.rendering.application.dto import RenderedSlideDTO, RenderJobDTO, VisualDiffResultDTO
from domains.rendering.domain.entities import RenderedSlide, RenderJob
from domains.rendering.domain.repositories import RenderJobRepository
from domains.rendering.domain.services import HTMLRenderer, VisualDiffService
from domains.rendering.domain.value_objects import RenderConfig

# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _rendered_slide_to_dto(s: RenderedSlide) -> RenderedSlideDTO:
    return RenderedSlideDTO(
        id=str(s.id),
        slide_id=str(s.slide_id),
        html=s.html,
        thumbnail_url=s.thumbnail_url,
        render_time_ms=s.render_time_ms,
    )


def _render_job_to_dto(job: RenderJob) -> RenderJobDTO:
    return RenderJobDTO(
        id=str(job.id),
        presentation_id=str(job.presentation_id),
        status=job.status.value,
        config_width=job.config.width,
        config_height=job.config.height,
        config_format=job.config.format,
        config_include_css=job.config.include_css,
        created_at=job.created_at.isoformat(),
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        rendered_slides=[_rendered_slide_to_dto(s) for s in job.rendered_slides],
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@dataclass
class RenderSlideCommand:
    """Render a single slide and return the rendered HTML."""

    html_renderer: HTMLRenderer

    async def execute(
        self,
        slide_id: uuid.UUID,
        slide_data: dict[str, Any],
        css_variables: str,
        config: RenderConfig | None = None,
    ) -> RenderedSlideDTO:
        if config is None:
            config = RenderConfig()
        start = time.monotonic_ns()
        html = await self.html_renderer.render(slide_data, css_variables)
        elapsed_ms = (time.monotonic_ns() - start) // 1_000_000
        slide = RenderedSlide(
            id=uuid.uuid4(),
            slide_id=slide_id,
            html=html,
            thumbnail_url=None,
            render_time_ms=elapsed_ms,
        )
        return _rendered_slide_to_dto(slide)


@dataclass
class RenderPresentationCommand:
    """Create a RenderJob and render all slides in a presentation."""

    repo: RenderJobRepository
    html_renderer: HTMLRenderer
    config: RenderConfig = field(default_factory=RenderConfig)

    async def execute(
        self,
        presentation_id: uuid.UUID,
        slides_data: list[dict[str, Any]],
        css_variables: str,
    ) -> RenderJobDTO:
        job = RenderJob(
            id=uuid.uuid4(),
            presentation_id=presentation_id,
            config=self.config,
        )
        await self.repo.save(job)
        job.start_rendering()

        try:
            for slide_info in slides_data:
                slide_id = uuid.UUID(str(slide_info["slide_id"]))
                start = time.monotonic_ns()
                html = await self.html_renderer.render(slide_info.get("data", {}), css_variables)
                elapsed_ms = (time.monotonic_ns() - start) // 1_000_000
                rendered = RenderedSlide(
                    id=uuid.uuid4(),
                    slide_id=slide_id,
                    html=html,
                    thumbnail_url=None,
                    render_time_ms=elapsed_ms,
                )
                job.add_rendered_slide(rendered)
            job.complete()
        except Exception:
            job.fail()
            await self.repo.save(job)
            raise

        await self.repo.save(job)
        return _render_job_to_dto(job)


@dataclass
class BatchRenderCommand:
    """Execute rendering for an existing RenderJob by its ID."""

    repo: RenderJobRepository
    html_renderer: HTMLRenderer
    slides_data: list[dict[str, Any]] = field(default_factory=list)
    css_variables: str = ""

    async def execute(self, render_job_id: uuid.UUID) -> RenderJobDTO:
        job = await self.repo.get(render_job_id)
        if job is None:
            raise ValueError(f"RenderJob '{render_job_id}' not found")

        job.start_rendering()

        try:
            for slide_info in self.slides_data:
                slide_id = uuid.UUID(str(slide_info["slide_id"]))
                start = time.monotonic_ns()
                html = await self.html_renderer.render(
                    slide_info.get("data", {}), self.css_variables
                )
                elapsed_ms = (time.monotonic_ns() - start) // 1_000_000
                rendered = RenderedSlide(
                    id=uuid.uuid4(),
                    slide_id=slide_id,
                    html=html,
                    thumbnail_url=None,
                    render_time_ms=elapsed_ms,
                )
                job.add_rendered_slide(rendered)
            job.complete()
        except Exception:
            job.fail()
            await self.repo.save(job)
            raise

        await self.repo.save(job)
        return _render_job_to_dto(job)


@dataclass
class ComputeVisualDiffCommand:
    """Compute visual diff between two rendered images."""

    diff_service: VisualDiffService = field(default_factory=VisualDiffService)

    async def execute(
        self,
        slide_id: uuid.UUID,
        image_a: bytes,
        image_b: bytes,
    ) -> VisualDiffResultDTO:
        result = self.diff_service.compute_diff(slide_id, image_a, image_b)
        return VisualDiffResultDTO(
            slide_id=str(result.slide_id),
            difference_percent=result.difference_percent,
            changed_regions=list(result.changed_regions),
        )
