"""MCP server for the style domain."""

from __future__ import annotations

import uuid

from domains.style.domain.repositories import StylePresetRepository, StyleProfileRepository
from shared.domain.events import EventBus
from shared.mcp.server_base import DomainMCPServer


def create_style_mcp_server(
    profile_repo: StyleProfileRepository,
    preset_repo: StylePresetRepository,
    event_bus: EventBus,
) -> DomainMCPServer:
    server = DomainMCPServer(name="style", port=9082)

    # ------------------------------------------------------------------
    # style.extract_from_file
    # ------------------------------------------------------------------

    @server.tool("style.extract_from_file")
    async def style_extract_from_file(file_path: str, name: str) -> dict:
        from domains.style.application.commands import ExtractStyleFromFileCommand

        cmd = ExtractStyleFromFileCommand(repo=profile_repo, event_bus=event_bus)
        result = await cmd.execute(file_path=file_path, name=name)
        return {
            "id": result.id,
            "name": result.name,
            "source": result.source,
            "created_at": result.created_at,
        }

    # ------------------------------------------------------------------
    # style.extract_from_url
    # ------------------------------------------------------------------

    @server.tool("style.extract_from_url")
    async def style_extract_from_url(url: str, name: str) -> dict:
        from domains.style.application.commands import ExtractStyleFromURLCommand

        cmd = ExtractStyleFromURLCommand(repo=profile_repo, event_bus=event_bus)
        result = await cmd.execute(url=url, name=name)
        return {
            "id": result.id,
            "name": result.name,
            "source": result.source,
            "created_at": result.created_at,
        }

    # ------------------------------------------------------------------
    # style.apply
    # ------------------------------------------------------------------

    @server.tool("style.apply")
    async def style_apply(presentation_id: str, profile_id: str) -> dict:
        from domains.style.application.commands import ApplyStyleCommand

        cmd = ApplyStyleCommand(profile_repo=profile_repo, event_bus=event_bus)
        await cmd.execute(
            presentation_id=uuid.UUID(presentation_id),
            profile_id=uuid.UUID(profile_id),
        )
        return {"status": "ok", "presentation_id": presentation_id, "profile_id": profile_id}

    # ------------------------------------------------------------------
    # style.presets.list
    # ------------------------------------------------------------------

    @server.tool("style.presets.list")
    async def style_presets_list(include_builtin: bool = True) -> list[dict]:
        from domains.style.application.queries import ListPresetsQuery

        query = ListPresetsQuery(preset_repo=preset_repo)
        results = await query.execute(include_builtin=include_builtin)
        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "is_builtin": r.is_builtin,
            }
            for r in results
        ]

    # ------------------------------------------------------------------
    # style.presets.create
    # ------------------------------------------------------------------

    @server.tool("style.presets.create")
    async def style_presets_create(name: str, description: str, profile_id: str) -> dict:
        from domains.style.application.commands import CreatePresetCommand

        cmd = CreatePresetCommand(
            profile_repo=profile_repo,
            preset_repo=preset_repo,
            event_bus=event_bus,
        )
        result = await cmd.execute(
            name=name,
            description=description,
            profile_id=uuid.UUID(profile_id),
        )
        return {
            "id": result.id,
            "name": result.name,
            "description": result.description,
            "is_builtin": result.is_builtin,
        }

    # ------------------------------------------------------------------
    # style.validate
    # ------------------------------------------------------------------

    @server.tool("style.validate")
    async def style_validate(
        profile_id: str,
        colors: list[str] | None = None,
        fonts: list[str] | None = None,
        bg_color: str = "",
    ) -> dict:
        from domains.style.application.commands import ValidateStyleCommand

        cmd = ValidateStyleCommand(profile_repo=profile_repo)
        rendered_data = {
            "colors": colors or [],
            "fonts": fonts or [],
            "bg_color": bg_color,
        }
        result = await cmd.execute(profile_id=uuid.UUID(profile_id), rendered_data=rendered_data)
        return {
            "profile_id": result.profile_id,
            "passed": result.passed,
            "criteria": result.criteria,
        }

    # ------------------------------------------------------------------
    # style.to_css
    # ------------------------------------------------------------------

    @server.tool("style.to_css")
    async def style_to_css(profile_id: str) -> dict:
        from domains.style.application.commands import GetCSSCommand

        cmd = GetCSSCommand(profile_repo=profile_repo)
        css = await cmd.execute(uuid.UUID(profile_id))
        return {"profile_id": profile_id, "css": css}

    # ------------------------------------------------------------------
    # style.to_tailwind
    # ------------------------------------------------------------------

    @server.tool("style.to_tailwind")
    async def style_to_tailwind(profile_id: str) -> dict:
        from domains.style.application.commands import GetTailwindCommand

        cmd = GetTailwindCommand(profile_repo=profile_repo)
        theme = await cmd.execute(uuid.UUID(profile_id))
        return {"profile_id": profile_id, "theme": theme}

    return server
