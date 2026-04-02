from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from domains.web_access.api.schemas import (
    ExtractRequest,
    FetchRequest,
    ScrapedPageResponse,
    ScreenshotRequest,
    SearchRequest,
    WebQueryResponse,
    WebResultSchema,
)
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


def create_web_access_router(
    search_adapter: WebSearchAdapter,
    fetch_adapter: WebFetchAdapter,
    screenshot_adapter: ScreenshotAdapter,
    query_repo: WebQueryRepository,
    event_bus: EventBus,
    cache_ttl_seconds: int = 3600,
) -> APIRouter:
    router = APIRouter(tags=["web"])

    @router.post("/search", response_model=WebQueryResponse)
    async def search_web(req: SearchRequest) -> WebQueryResponse:
        engine = SearchEngine(req.engine)
        cmd = SearchWebCommand(
            search_adapter=search_adapter,
            query_repo=query_repo,
            event_bus=event_bus,
            cache_ttl_seconds=cache_ttl_seconds,
        )
        dto = await cmd.execute(query=req.query, engine=engine, max_results=req.max_results)
        return WebQueryResponse(
            id=dto.id,
            query=dto.query,
            engine=dto.engine,
            results=[
                WebResultSchema(title=r.title, url=r.url, snippet=r.snippet) for r in dto.results
            ],
            created_at=dto.created_at,
            cached_until=dto.cached_until,
        )

    @router.post("/fetch", response_model=ScrapedPageResponse)
    async def fetch_url(req: FetchRequest) -> ScrapedPageResponse:
        fmt = ContentFormat(req.format)
        cmd = FetchURLCommand(fetch_adapter=fetch_adapter, event_bus=event_bus)
        dto = await cmd.execute(url=req.url, format=fmt)
        return ScrapedPageResponse(
            id=dto.id,
            url=dto.url,
            content=dto.content,
            format=dto.format,
            fetched_at=dto.fetched_at,
        )

    @router.post("/screenshot")
    async def take_screenshot(req: ScreenshotRequest) -> Response:
        cmd = TakeScreenshotCommand(screenshot_adapter=screenshot_adapter, event_bus=event_bus)
        image_bytes = await cmd.execute(
            url=req.url,
            viewport_width=req.viewport_width,
            viewport_height=req.viewport_height,
        )
        return Response(content=image_bytes, media_type="image/png")

    @router.post("/extract")
    async def extract_data(req: ExtractRequest) -> dict:
        cmd = ExtractDataCommand(fetch_adapter=fetch_adapter, event_bus=event_bus)
        return await cmd.execute(url=req.url)

    return router
