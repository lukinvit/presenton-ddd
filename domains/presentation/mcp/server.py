"""MCP server for the presentation domain."""

from __future__ import annotations

import uuid

from domains.presentation.domain.repositories import PresentationRepository
from domains.presentation.domain.services import PresentationService
from shared.domain.events import EventBus
from shared.mcp.server_base import DomainMCPServer


def create_presentation_mcp_server(
    repo: PresentationRepository,
    event_bus: EventBus,
) -> DomainMCPServer:
    server = DomainMCPServer(name="presentation", port=9081)
    service = PresentationService()

    # ------------------------------------------------------------------
    # Presentation tools
    # ------------------------------------------------------------------

    @server.tool("presentation.create")
    async def presentation_create(title: str, description: str = "") -> dict:
        from domains.presentation.application.commands import CreatePresentationCommand

        cmd = CreatePresentationCommand(repo=repo, event_bus=event_bus, service=service)
        result = await cmd.execute(title=title, description=description)
        return {
            "id": result.id,
            "title": result.title,
            "description": result.description,
            "status": result.status,
        }

    @server.tool("presentation.get")
    async def presentation_get(presentation_id: str) -> dict:
        from domains.presentation.application.queries import GetPresentationQuery

        query = GetPresentationQuery(repo=repo)
        result = await query.execute(uuid.UUID(presentation_id))
        return {
            "id": result.id,
            "title": result.title,
            "description": result.description,
            "status": result.status,
            "slide_count": len(result.slides),
            "created_at": result.created_at,
            "updated_at": result.updated_at,
        }

    @server.tool("presentation.list")
    async def presentation_list(limit: int = 50, offset: int = 0) -> list[dict]:
        from domains.presentation.application.queries import ListPresentationsQuery

        query = ListPresentationsQuery(repo=repo)
        results = await query.execute(limit=limit, offset=offset)
        return [
            {
                "id": r.id,
                "title": r.title,
                "status": r.status,
                "slide_count": len(r.slides),
            }
            for r in results
        ]

    @server.tool("presentation.update")
    async def presentation_update(
        presentation_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> dict:
        from domains.presentation.application.commands import UpdatePresentationCommand

        cmd = UpdatePresentationCommand(repo=repo, event_bus=event_bus)
        result = await cmd.execute(
            presentation_id=uuid.UUID(presentation_id),
            title=title,
            description=description,
            status=status,
        )
        return {"id": result.id, "title": result.title, "status": result.status}

    @server.tool("presentation.delete")
    async def presentation_delete(presentation_id: str) -> dict:
        pid = uuid.UUID(presentation_id)
        presentation = await repo.get(pid)
        if presentation is None:
            raise ValueError(f"Presentation '{presentation_id}' not found")
        await repo.delete(pid)
        return {"deleted": presentation_id}

    # ------------------------------------------------------------------
    # Slide tools
    # ------------------------------------------------------------------

    @server.tool("slide.add")
    async def slide_add(
        presentation_id: str,
        title: str,
        layout_type: str = "content",
        index: int | None = None,
        speaker_notes: str = "",
    ) -> dict:
        from domains.presentation.application.commands import AddSlideCommand

        cmd = AddSlideCommand(repo=repo, event_bus=event_bus, service=service)
        result = await cmd.execute(
            presentation_id=uuid.UUID(presentation_id),
            title=title,
            layout_type=layout_type,
            index=index,
            speaker_notes=speaker_notes,
        )
        return {
            "id": result.id,
            "presentation_id": result.presentation_id,
            "index": result.index,
            "title": result.title,
            "layout_type": result.layout_type,
        }

    @server.tool("slide.update")
    async def slide_update(
        presentation_id: str,
        slide_id: str,
        title: str | None = None,
        speaker_notes: str | None = None,
    ) -> dict:
        from domains.presentation.application.commands import UpdateSlideCommand

        cmd = UpdateSlideCommand(repo=repo, event_bus=event_bus)
        result = await cmd.execute(
            presentation_id=uuid.UUID(presentation_id),
            slide_id=uuid.UUID(slide_id),
            title=title,
            speaker_notes=speaker_notes,
        )
        return {"id": result.id, "title": result.title, "index": result.index}

    @server.tool("slide.remove")
    async def slide_remove(presentation_id: str, slide_id: str) -> dict:
        from domains.presentation.application.commands import RemoveSlideCommand

        cmd = RemoveSlideCommand(repo=repo, event_bus=event_bus)
        await cmd.execute(
            presentation_id=uuid.UUID(presentation_id),
            slide_id=uuid.UUID(slide_id),
        )
        return {"removed": slide_id}

    @server.tool("slide.reorder")
    async def slide_reorder(presentation_id: str, slide_ids: list[str]) -> dict:
        from domains.presentation.application.commands import ReorderSlidesCommand

        cmd = ReorderSlidesCommand(repo=repo, event_bus=event_bus, service=service)
        await cmd.execute(
            presentation_id=uuid.UUID(presentation_id),
            slide_ids=[uuid.UUID(sid) for sid in slide_ids],
        )
        return {"status": "ok"}

    return server
