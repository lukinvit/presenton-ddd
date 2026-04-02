from __future__ import annotations

import base64

from domains.web_access.application.commands import (
    ExtractDataCommand,
    FetchURLCommand,
    SearchWebCommand,
    TakeScreenshotCommand,
)
from domains.web_access.domain.repositories import WebQueryRepository
from domains.web_access.domain.services import ScreenshotAdapter, WebFetchAdapter, WebSearchAdapter
from domains.web_access.domain.value_objects import ContentFormat, SearchEngine
from shared.domain.events import EventBus
from shared.mcp.server_base import DomainMCPServer


def create_web_access_mcp_server(
    search_adapter: WebSearchAdapter,
    fetch_adapter: WebFetchAdapter,
    screenshot_adapter: ScreenshotAdapter,
    query_repo: WebQueryRepository,
    event_bus: EventBus,
    cache_ttl_seconds: int = 3600,
) -> DomainMCPServer:
    server = DomainMCPServer(name="web_access", port=9071)

    @server.tool("web.search")
    async def web_search(query: str, engine: str = "duckduckgo", max_results: int = 10) -> dict:
        search_engine = SearchEngine(engine)
        cmd = SearchWebCommand(
            search_adapter=search_adapter,
            query_repo=query_repo,
            event_bus=event_bus,
            cache_ttl_seconds=cache_ttl_seconds,
        )
        dto = await cmd.execute(query=query, engine=search_engine, max_results=max_results)
        return {
            "id": str(dto.id),
            "query": dto.query,
            "engine": dto.engine,
            "results": [
                {"title": r.title, "url": r.url, "snippet": r.snippet} for r in dto.results
            ],
        }

    @server.tool("web.fetch")
    async def web_fetch(url: str, format: str = "markdown") -> dict:
        fmt = ContentFormat(format)
        cmd = FetchURLCommand(fetch_adapter=fetch_adapter, event_bus=event_bus)
        dto = await cmd.execute(url=url, format=fmt)
        return {
            "id": str(dto.id),
            "url": dto.url,
            "content": dto.content,
            "format": dto.format,
        }

    @server.tool("web.screenshot")
    async def web_screenshot(
        url: str, viewport_width: int = 1920, viewport_height: int = 1080
    ) -> dict:
        cmd = TakeScreenshotCommand(screenshot_adapter=screenshot_adapter, event_bus=event_bus)
        image_bytes = await cmd.execute(
            url=url,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
        )
        return {
            "url": url,
            "image_base64": base64.b64encode(image_bytes).decode("utf-8"),
            "size_bytes": len(image_bytes),
        }

    @server.tool("web.extract_data")
    async def web_extract_data(url: str) -> dict:
        cmd = ExtractDataCommand(fetch_adapter=fetch_adapter, event_bus=event_bus)
        return await cmd.execute(url=url)

    return server
