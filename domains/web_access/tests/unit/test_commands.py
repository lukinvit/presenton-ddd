from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from domains.web_access.application.commands import (
    ExtractDataCommand,
    FetchURLCommand,
    SearchWebCommand,
    TakeScreenshotCommand,
)
from domains.web_access.application.dto import ScrapedPageDTO, WebQueryDTO
from domains.web_access.domain.entities import WebQuery, WebResult
from domains.web_access.domain.value_objects import ContentFormat, SearchEngine


class TestSearchWebCommand:
    @pytest.mark.asyncio
    async def test_searches_and_returns_results(self) -> None:
        search_adapter = AsyncMock()
        search_adapter.search.return_value = [
            WebResult(title="Result 1", url="https://r1.com", snippet="First result"),
            WebResult(title="Result 2", url="https://r2.com", snippet="Second result"),
        ]
        query_repo = AsyncMock()
        query_repo.find_cached.return_value = None
        event_bus = AsyncMock()

        cmd = SearchWebCommand(
            search_adapter=search_adapter,
            query_repo=query_repo,
            event_bus=event_bus,
        )
        dto = await cmd.execute(query="python tutorials", engine=SearchEngine.DUCKDUCKGO)

        assert isinstance(dto, WebQueryDTO)
        assert dto.query == "python tutorials"
        assert dto.engine == "duckduckgo"
        assert len(dto.results) == 2
        assert dto.results[0].title == "Result 1"

    @pytest.mark.asyncio
    async def test_saves_results_to_repo(self) -> None:
        search_adapter = AsyncMock()
        search_adapter.search.return_value = [
            WebResult(title="T", url="https://t.com", snippet="S"),
        ]
        query_repo = AsyncMock()
        query_repo.find_cached.return_value = None
        event_bus = AsyncMock()

        cmd = SearchWebCommand(
            search_adapter=search_adapter,
            query_repo=query_repo,
            event_bus=event_bus,
        )
        await cmd.execute(query="test")
        query_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_publishes_event(self) -> None:
        search_adapter = AsyncMock()
        search_adapter.search.return_value = []
        query_repo = AsyncMock()
        query_repo.find_cached.return_value = None
        event_bus = AsyncMock()

        cmd = SearchWebCommand(
            search_adapter=search_adapter,
            query_repo=query_repo,
            event_bus=event_bus,
        )
        await cmd.execute(query="event test")
        event_bus.publish.assert_called_once()
        published = event_bus.publish.call_args[0][0]
        assert published.event_type == "WebSearched"

    @pytest.mark.asyncio
    async def test_returns_cached_result_when_valid(self) -> None:
        cached_query = WebQuery(
            id=uuid.uuid4(),
            query="cached",
            engine=SearchEngine.GOOGLE,
            results=[WebResult(title="Cached", url="https://c.com", snippet="Cached snippet")],
            cached_until=datetime.now(UTC) + timedelta(hours=1),
        )
        search_adapter = AsyncMock()
        query_repo = AsyncMock()
        query_repo.find_cached.return_value = cached_query
        event_bus = AsyncMock()

        cmd = SearchWebCommand(
            search_adapter=search_adapter,
            query_repo=query_repo,
            event_bus=event_bus,
        )
        dto = await cmd.execute(query="cached", engine=SearchEngine.GOOGLE)
        search_adapter.search.assert_not_called()
        assert dto.results[0].title == "Cached"

    @pytest.mark.asyncio
    async def test_re_searches_when_cache_expired(self) -> None:
        expired_query = WebQuery(
            id=uuid.uuid4(),
            query="expired",
            engine=SearchEngine.DUCKDUCKGO,
            results=[],
            cached_until=datetime.now(UTC) - timedelta(seconds=1),
        )
        search_adapter = AsyncMock()
        search_adapter.search.return_value = [
            WebResult(title="Fresh", url="https://fresh.com", snippet="Fresh result"),
        ]
        query_repo = AsyncMock()
        query_repo.find_cached.return_value = expired_query
        event_bus = AsyncMock()

        cmd = SearchWebCommand(
            search_adapter=search_adapter,
            query_repo=query_repo,
            event_bus=event_bus,
        )
        dto = await cmd.execute(query="expired")
        search_adapter.search.assert_called_once()
        assert dto.results[0].title == "Fresh"


class TestFetchURLCommand:
    @pytest.mark.asyncio
    async def test_fetches_and_returns_page(self) -> None:
        fetch_adapter = AsyncMock()
        fetch_adapter.fetch.return_value = "# Page Title\n\nContent here."
        event_bus = AsyncMock()

        cmd = FetchURLCommand(fetch_adapter=fetch_adapter, event_bus=event_bus)
        dto = await cmd.execute(url="https://example.com", format=ContentFormat.MARKDOWN)

        assert isinstance(dto, ScrapedPageDTO)
        assert dto.url == "https://example.com"
        assert dto.content == "# Page Title\n\nContent here."
        assert dto.format == "markdown"

    @pytest.mark.asyncio
    async def test_publishes_page_fetched_event(self) -> None:
        fetch_adapter = AsyncMock()
        fetch_adapter.fetch.return_value = "<html></html>"
        event_bus = AsyncMock()

        cmd = FetchURLCommand(fetch_adapter=fetch_adapter, event_bus=event_bus)
        await cmd.execute(url="https://example.com", format=ContentFormat.HTML)

        event_bus.publish.assert_called_once()
        published = event_bus.publish.call_args[0][0]
        assert published.event_type == "PageFetched"
        assert published.payload["url"] == "https://example.com"
        assert published.payload["format"] == "html"

    @pytest.mark.asyncio
    async def test_default_format_is_markdown(self) -> None:
        fetch_adapter = AsyncMock()
        fetch_adapter.fetch.return_value = "content"
        event_bus = AsyncMock()

        cmd = FetchURLCommand(fetch_adapter=fetch_adapter, event_bus=event_bus)
        dto = await cmd.execute(url="https://example.com")
        assert dto.format == "markdown"
        fetch_adapter.fetch.assert_called_once_with(
            "https://example.com", format=ContentFormat.MARKDOWN
        )


class TestTakeScreenshotCommand:
    @pytest.mark.asyncio
    async def test_returns_image_bytes(self) -> None:
        screenshot_adapter = AsyncMock()
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        screenshot_adapter.screenshot.return_value = fake_png
        event_bus = AsyncMock()

        cmd = TakeScreenshotCommand(screenshot_adapter=screenshot_adapter, event_bus=event_bus)
        result = await cmd.execute(url="https://example.com")

        assert result == fake_png
        screenshot_adapter.screenshot.assert_called_once_with(
            "https://example.com", viewport_width=1920, viewport_height=1080
        )

    @pytest.mark.asyncio
    async def test_publishes_screenshot_event(self) -> None:
        screenshot_adapter = AsyncMock()
        screenshot_adapter.screenshot.return_value = b"PNG_DATA"
        event_bus = AsyncMock()

        cmd = TakeScreenshotCommand(screenshot_adapter=screenshot_adapter, event_bus=event_bus)
        await cmd.execute(url="https://example.com", viewport_width=1280, viewport_height=720)

        event_bus.publish.assert_called_once()
        published = event_bus.publish.call_args[0][0]
        assert published.event_type == "ScreenshotTaken"
        assert published.payload["url"] == "https://example.com"
        assert published.payload["viewport_width"] == 1280

    @pytest.mark.asyncio
    async def test_custom_viewport(self) -> None:
        screenshot_adapter = AsyncMock()
        screenshot_adapter.screenshot.return_value = b"PNG"
        event_bus = AsyncMock()

        cmd = TakeScreenshotCommand(screenshot_adapter=screenshot_adapter, event_bus=event_bus)
        await cmd.execute(url="https://example.com", viewport_width=800, viewport_height=600)

        screenshot_adapter.screenshot.assert_called_once_with(
            "https://example.com", viewport_width=800, viewport_height=600
        )


class TestExtractDataCommand:
    @pytest.mark.asyncio
    async def test_extracts_data_from_url(self) -> None:
        fetch_adapter = AsyncMock()
        fetch_adapter.fetch.return_value = "Some page text content"
        event_bus = AsyncMock()

        cmd = ExtractDataCommand(fetch_adapter=fetch_adapter, event_bus=event_bus)
        result = await cmd.execute(url="https://example.com")

        assert isinstance(result, dict)
        assert result["url"] == "https://example.com"
        assert result["content"] == "Some page text content"

    @pytest.mark.asyncio
    async def test_fetches_as_text_format(self) -> None:
        fetch_adapter = AsyncMock()
        fetch_adapter.fetch.return_value = "text content"
        event_bus = AsyncMock()

        cmd = ExtractDataCommand(fetch_adapter=fetch_adapter, event_bus=event_bus)
        await cmd.execute(url="https://example.com")

        fetch_adapter.fetch.assert_called_once_with(
            "https://example.com", format=ContentFormat.TEXT
        )

    @pytest.mark.asyncio
    async def test_publishes_data_extracted_event(self) -> None:
        fetch_adapter = AsyncMock()
        fetch_adapter.fetch.return_value = "text"
        event_bus = AsyncMock()

        cmd = ExtractDataCommand(fetch_adapter=fetch_adapter, event_bus=event_bus)
        await cmd.execute(url="https://example.com")

        event_bus.publish.assert_called_once()
        published = event_bus.publish.call_args[0][0]
        assert published.event_type == "DataExtracted"
        assert published.payload["url"] == "https://example.com"
