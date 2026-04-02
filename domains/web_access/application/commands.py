from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from domains.web_access.application.dto import ScrapedPageDTO, WebQueryDTO, WebResultDTO
from domains.web_access.domain.entities import ScrapedPage, WebQuery
from domains.web_access.domain.repositories import WebQueryRepository
from domains.web_access.domain.services import ScreenshotAdapter, WebFetchAdapter, WebSearchAdapter
from domains.web_access.domain.value_objects import ContentFormat, SearchEngine
from shared.domain.events import DomainEvent, EventBus


@dataclass
class SearchWebCommand:
    """Search the web and cache results."""

    search_adapter: WebSearchAdapter
    query_repo: WebQueryRepository
    event_bus: EventBus
    cache_ttl_seconds: int = 3600

    async def execute(
        self,
        query: str,
        engine: SearchEngine = SearchEngine.DUCKDUCKGO,
        max_results: int = 10,
    ) -> WebQueryDTO:
        cached = await self.query_repo.find_cached(query, engine)
        if cached is not None and cached.is_cache_valid():
            return _to_query_dto(cached)

        raw_results = await self.search_adapter.search(query, max_results=max_results)
        web_query = WebQuery(
            id=uuid.uuid4(),
            query=query,
            engine=engine,
            cached_until=datetime.now(UTC) + timedelta(seconds=self.cache_ttl_seconds),
        )
        web_query.set_results(raw_results)
        await self.query_repo.save(web_query)

        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=web_query.id,
                event_type="WebSearched",
                payload={"query": query, "engine": engine.value, "count": len(raw_results)},
            )
        )
        return _to_query_dto(web_query)


@dataclass
class FetchURLCommand:
    """Fetch a URL and convert its content to the requested format."""

    fetch_adapter: WebFetchAdapter
    event_bus: EventBus

    async def execute(
        self,
        url: str,
        format: ContentFormat = ContentFormat.MARKDOWN,
    ) -> ScrapedPageDTO:
        content = await self.fetch_adapter.fetch(url, format=format)
        page = ScrapedPage.create(url=url, content=content, format=format)

        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=page.id,
                event_type="PageFetched",
                payload={"url": url, "format": format.value},
            )
        )
        return _to_page_dto(page)


@dataclass
class TakeScreenshotCommand:
    """Capture a screenshot of a URL."""

    screenshot_adapter: ScreenshotAdapter
    event_bus: EventBus

    async def execute(
        self,
        url: str,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ) -> bytes:
        image_bytes = await self.screenshot_adapter.screenshot(
            url,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
        )

        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=uuid.uuid4(),
                event_type="ScreenshotTaken",
                payload={
                    "url": url,
                    "viewport_width": viewport_width,
                    "viewport_height": viewport_height,
                    "size_bytes": len(image_bytes),
                },
            )
        )
        return image_bytes


@dataclass
class ExtractDataCommand:
    """Fetch a URL and extract structured data from its content."""

    fetch_adapter: WebFetchAdapter
    event_bus: EventBus

    async def execute(self, url: str) -> dict[str, Any]:
        content = await self.fetch_adapter.fetch(url, format=ContentFormat.TEXT)

        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=uuid.uuid4(),
                event_type="DataExtracted",
                payload={"url": url},
            )
        )
        return {"url": url, "content": content}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_query_dto(web_query: WebQuery) -> WebQueryDTO:
    return WebQueryDTO(
        id=web_query.id,
        query=web_query.query,
        engine=web_query.engine.value,
        results=[
            WebResultDTO(title=r.title, url=r.url, snippet=r.snippet) for r in web_query.results
        ],
        created_at=web_query.created_at,
        cached_until=web_query.cached_until,
    )


def _to_page_dto(page: ScrapedPage) -> ScrapedPageDTO:
    return ScrapedPageDTO(
        id=page.id,
        url=page.url,
        content=page.content,
        format=page.format.value,
        fetched_at=page.fetched_at,
    )
