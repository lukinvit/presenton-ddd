"""MCP server for the rendering domain."""

from __future__ import annotations

import uuid
from typing import Any

from domains.rendering.domain.repositories import RenderJobRepository
from domains.rendering.domain.services import HTMLRenderer, VisualDiffService
from domains.rendering.domain.value_objects import RenderConfig
from shared.mcp.server_base import DomainMCPServer


def create_rendering_mcp_server(
    repo: RenderJobRepository,
    html_renderer: HTMLRenderer,
    diff_service: VisualDiffService | None = None,
) -> DomainMCPServer:
    server = DomainMCPServer(name="rendering", port=9084)
    _diff_service = diff_service or VisualDiffService()

    @server.tool("rendering.render_slide")
    async def rendering_render_slide(
        slide_id: str,
        slide_data: dict[str, Any] | None = None,
        css_variables: str = "",
        width: int = 1920,
        height: int = 1080,
    ) -> dict[str, Any]:
        from domains.rendering.application.commands import RenderSlideCommand

        config = RenderConfig(width=width, height=height)
        cmd = RenderSlideCommand(html_renderer=html_renderer)
        result = await cmd.execute(
            slide_id=uuid.UUID(slide_id),
            slide_data=slide_data or {},
            css_variables=css_variables,
            config=config,
        )
        return {
            "id": result.id,
            "slide_id": result.slide_id,
            "html": result.html,
            "thumbnail_url": result.thumbnail_url,
            "render_time_ms": result.render_time_ms,
        }

    @server.tool("rendering.render_preview")
    async def rendering_render_preview(
        presentation_id: str,
        slides_data: list[dict[str, Any]] | None = None,
        css_variables: str = "",
    ) -> dict[str, Any]:
        from domains.rendering.application.commands import RenderPresentationCommand

        cmd = RenderPresentationCommand(
            repo=repo,
            html_renderer=html_renderer,
        )
        result = await cmd.execute(
            presentation_id=uuid.UUID(presentation_id),
            slides_data=slides_data or [],
            css_variables=css_variables,
        )
        return {
            "id": result.id,
            "presentation_id": result.presentation_id,
            "status": result.status,
            "slide_count": len(result.rendered_slides),
        }

    @server.tool("rendering.visual_diff")
    async def rendering_visual_diff(
        slide_id: str,
        image_a_hex: str,
        image_b_hex: str,
    ) -> dict[str, Any]:
        from domains.rendering.application.commands import ComputeVisualDiffCommand

        cmd = ComputeVisualDiffCommand(diff_service=_diff_service)
        image_a = bytes.fromhex(image_a_hex)
        image_b = bytes.fromhex(image_b_hex)
        result = await cmd.execute(
            slide_id=uuid.UUID(slide_id),
            image_a=image_a,
            image_b=image_b,
        )
        return {
            "slide_id": result.slide_id,
            "difference_percent": result.difference_percent,
            "changed_regions": result.changed_regions,
        }

    @server.tool("rendering.batch_render")
    async def rendering_batch_render(
        render_job_id: str,
        slides_data: list[dict[str, Any]] | None = None,
        css_variables: str = "",
    ) -> dict[str, Any]:
        from domains.rendering.application.commands import BatchRenderCommand

        cmd = BatchRenderCommand(
            repo=repo,
            html_renderer=html_renderer,
            slides_data=slides_data or [],
            css_variables=css_variables,
        )
        result = await cmd.execute(render_job_id=uuid.UUID(render_job_id))
        return {
            "id": result.id,
            "status": result.status,
            "slide_count": len(result.rendered_slides),
            "completed_at": result.completed_at,
        }

    return server
