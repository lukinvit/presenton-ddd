"""MCP server for the media domain."""

from __future__ import annotations

from typing import Any

from domains.media.domain.adapters import ImageGenerationAdapter, ImageSearchAdapter
from domains.media.domain.repositories import InfographicTemplateRepository, MediaAssetRepository
from domains.media.domain.services import SVGInfographicService
from shared.mcp.server_base import DomainMCPServer


def create_media_mcp_server(
    asset_repo: MediaAssetRepository,
    template_repo: InfographicTemplateRepository,
    image_search_adapter: ImageSearchAdapter,
    image_generation_adapter: ImageGenerationAdapter,
    svg_service: SVGInfographicService | None = None,
) -> DomainMCPServer:
    server = DomainMCPServer(name="media", port=9084)

    _svg_service = svg_service or SVGInfographicService()

    # ------------------------------------------------------------------
    # Image search
    # ------------------------------------------------------------------

    @server.tool("media.search_images")
    async def media_search_images(
        query: str,
        max_results: int = 10,
        source: str | None = None,
    ) -> list[dict[str, Any]]:
        from domains.media.application.commands import SearchImagesCommand

        cmd = SearchImagesCommand(repo=asset_repo, adapter=image_search_adapter)
        results = await cmd.execute(query=query, max_results=max_results, source=source)
        return [
            {"id": r.id, "url": r.url, "source": r.source, "metadata": r.metadata} for r in results
        ]

    # ------------------------------------------------------------------
    # Image generation
    # ------------------------------------------------------------------

    @server.tool("media.generate_image")
    async def media_generate_image(
        prompt: str,
        provider: str | None = None,
        size: str = "1024x1024",
    ) -> dict[str, Any]:
        from domains.media.application.commands import GenerateImageCommand

        cmd = GenerateImageCommand(repo=asset_repo, adapter=image_generation_adapter)
        result = await cmd.execute(prompt=prompt, provider=provider, size=size)
        return {"id": result.id, "url": result.url, "source": result.source}

    # ------------------------------------------------------------------
    # Infographic
    # ------------------------------------------------------------------

    @server.tool("media.create_infographic")
    async def media_create_infographic(
        infographic_type: str,
        data: dict[str, Any],
        template_id: str | None = None,
    ) -> dict[str, Any]:
        from domains.media.application.commands import CreateInfographicCommand

        cmd = CreateInfographicCommand(
            repo=asset_repo,
            template_repo=template_repo,
            svg_service=_svg_service,
        )
        result = await cmd.execute(
            infographic_type=infographic_type,
            data=data,
            template_id=template_id,
        )
        return {
            "id": result.id,
            "url": result.url,
            "type": result.type,
            "metadata": result.metadata,
        }

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    @server.tool("media.infographic_templates.list")
    async def media_infographic_templates_list() -> list[dict[str, Any]]:
        from domains.media.application.commands import ListInfographicTemplatesQuery

        query = ListInfographicTemplatesQuery(template_repo=template_repo)
        results = await query.execute()
        return [
            {
                "id": r.id,
                "name": r.name,
                "required_data_fields": r.required_data_fields,
                "is_builtin": r.is_builtin,
            }
            for r in results
        ]

    # ------------------------------------------------------------------
    # Icon search
    # ------------------------------------------------------------------

    @server.tool("media.icons.search")
    async def media_icons_search(
        query: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        from domains.media.application.commands import SearchIconsCommand

        cmd = SearchIconsCommand(repo=asset_repo, adapter=image_search_adapter)
        results = await cmd.execute(query=query, max_results=max_results)
        return [
            {"id": r.id, "url": r.url, "source": r.source, "metadata": r.metadata} for r in results
        ]

    return server
