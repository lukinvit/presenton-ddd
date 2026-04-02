from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from domains.web_access.api.router import create_web_access_router
from domains.web_access.domain.entities import WebResult


def _make_fake_png() -> bytes:
    # Minimal valid PNG header + IHDR chunk stub
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 50


def create_test_app() -> FastAPI:
    app = FastAPI()

    search_adapter = AsyncMock()
    search_adapter.search.return_value = [
        WebResult(title="Test Result", url="https://test.com", snippet="A test snippet"),
    ]

    fetch_adapter = AsyncMock()
    fetch_adapter.fetch.return_value = "# Fetched Page\n\nContent."

    screenshot_adapter = AsyncMock()
    screenshot_adapter.screenshot.return_value = _make_fake_png()

    query_repo = AsyncMock()
    query_repo.find_cached.return_value = None

    event_bus = AsyncMock()

    router = create_web_access_router(
        search_adapter=search_adapter,
        fetch_adapter=fetch_adapter,
        screenshot_adapter=screenshot_adapter,
        query_repo=query_repo,
        event_bus=event_bus,
    )
    app.include_router(router)
    return app


class TestSearchEndpoint:
    @pytest.mark.asyncio
    async def test_search_returns_results(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/search",
                json={"query": "python web scraping", "engine": "duckduckgo", "max_results": 5},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "python web scraping"
        assert data["engine"] == "duckduckgo"
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Test Result"

    @pytest.mark.asyncio
    async def test_search_defaults_to_duckduckgo(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/search", json={"query": "anything"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["engine"] == "duckduckgo"

    @pytest.mark.asyncio
    async def test_search_invalid_engine_returns_422(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/search", json={"query": "test", "engine": "nonexistent_engine"}
            )
        assert resp.status_code == 422


class TestFetchEndpoint:
    @pytest.mark.asyncio
    async def test_fetch_returns_page_content(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/fetch", json={"url": "https://example.com", "format": "markdown"}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["url"] == "https://example.com"
        assert "Fetched Page" in data["content"]
        assert data["format"] == "markdown"

    @pytest.mark.asyncio
    async def test_fetch_invalid_format_returns_422(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/fetch", json={"url": "https://example.com", "format": "pdf"})
        assert resp.status_code == 422


class TestScreenshotEndpoint:
    @pytest.mark.asyncio
    async def test_screenshot_returns_png(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/screenshot", json={"url": "https://example.com"})
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert resp.content[:8] == b"\x89PNG\r\n\x1a\n"

    @pytest.mark.asyncio
    async def test_screenshot_custom_viewport(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/screenshot",
                json={"url": "https://example.com", "viewport_width": 1280, "viewport_height": 720},
            )
        assert resp.status_code == 200


class TestExtractEndpoint:
    @pytest.mark.asyncio
    async def test_extract_returns_dict(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/extract", json={"url": "https://example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["url"] == "https://example.com"
        assert "content" in data
