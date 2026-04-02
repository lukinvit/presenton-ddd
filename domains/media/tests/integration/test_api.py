"""Integration tests for the media FastAPI router."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from domains.media.api.router import create_media_router
from domains.media.domain.entities import MediaAsset
from domains.media.domain.services import SVGInfographicService

# ---------------------------------------------------------------------------
# Fake repos / adapters
# ---------------------------------------------------------------------------


def _make_asset_repo() -> AsyncMock:
    store: dict[uuid.UUID, MediaAsset] = {}
    repo = AsyncMock()

    async def save(asset: MediaAsset) -> None:
        store[asset.id] = asset

    async def get(asset_id: uuid.UUID) -> MediaAsset | None:
        return store.get(asset_id)

    async def list_all(limit: int = 50, offset: int = 0) -> list[MediaAsset]:
        items = list(store.values())
        return items[offset : offset + limit]

    async def delete(asset_id: uuid.UUID) -> None:
        store.pop(asset_id, None)

    repo.save = AsyncMock(side_effect=save)
    repo.get = AsyncMock(side_effect=get)
    repo.list_all = AsyncMock(side_effect=list_all)
    repo.delete = AsyncMock(side_effect=delete)
    return repo


def _make_template_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.list_all = AsyncMock(return_value=[])
    repo.get = AsyncMock(return_value=None)
    repo.save = AsyncMock()
    return repo


def _make_search_adapter(results: list[dict] | None = None) -> AsyncMock:
    adapter = AsyncMock()
    default = [
        {"url": "https://example.com/img1.jpg", "source": "pexels"},
        {"url": "https://example.com/img2.jpg", "source": "pexels"},
    ]
    adapter.search = AsyncMock(return_value=default if results is None else results)
    return adapter


def _make_generation_adapter(url: str = "https://ai.com/generated.jpg") -> AsyncMock:
    adapter = AsyncMock()
    adapter.generate = AsyncMock(return_value=url)
    return adapter


def create_test_app(
    search_adapter: AsyncMock | None = None,
    generation_adapter: AsyncMock | None = None,
) -> FastAPI:
    app = FastAPI()
    router = create_media_router(
        asset_repo=_make_asset_repo(),
        template_repo=_make_template_repo(),
        image_search_adapter=search_adapter or _make_search_adapter(),
        image_generation_adapter=generation_adapter or _make_generation_adapter(),
        svg_service=SVGInfographicService(),
    )
    app.include_router(router)
    return app


# ---------------------------------------------------------------------------
# Tests: POST /media/search
# ---------------------------------------------------------------------------


class TestSearchImages:
    async def test_returns_200_with_results(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/media/search", json={"query": "cats", "max_results": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["type"] == "image"

    async def test_returns_empty_list_when_no_results(self) -> None:
        app = create_test_app(search_adapter=_make_search_adapter([]))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/media/search", json={"query": "nothing"})
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_result_has_required_fields(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/media/search", json={"query": "dogs"})
        item = resp.json()[0]
        for field in ("id", "type", "url", "source"):
            assert field in item


# ---------------------------------------------------------------------------
# Tests: POST /media/generate
# ---------------------------------------------------------------------------


class TestGenerateImage:
    async def test_returns_201_with_asset(self) -> None:
        app = create_test_app(generation_adapter=_make_generation_adapter("https://ai.com/abc.jpg"))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/media/generate",
                json={"prompt": "a beautiful landscape", "provider": "dalle"},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["url"] == "https://ai.com/abc.jpg"
        assert data["type"] == "image"

    async def test_result_has_id(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/media/generate", json={"prompt": "test"})
        assert "id" in resp.json()


# ---------------------------------------------------------------------------
# Tests: POST /media/infographic
# ---------------------------------------------------------------------------


class TestCreateInfographic:
    async def test_pie_chart_returns_201(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/media/infographic",
                json={
                    "type": "pie_chart",
                    "data": {
                        "title": "Sales",
                        "slices": [{"label": "A", "value": 60}, {"label": "B", "value": 40}],
                    },
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "infographic"
        assert data["url"].startswith("data:image/svg+xml;base64,")

    async def test_bar_chart_returns_201(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/media/infographic",
                json={
                    "type": "bar_chart",
                    "data": {
                        "title": "Revenue",
                        "bars": [{"label": "Q1", "value": 100}, {"label": "Q2", "value": 150}],
                    },
                },
            )
        assert resp.status_code == 201

    async def test_unknown_type_returns_400(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/media/infographic",
                json={"type": "nonexistent_chart", "data": {}},
            )
        assert resp.status_code == 400

    async def test_timeline_returns_201(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/media/infographic",
                json={
                    "type": "timeline",
                    "data": {
                        "title": "History",
                        "events": [
                            {"label": "Founding", "date": "1900"},
                            {"label": "Growth", "date": "1950"},
                        ],
                    },
                },
            )
        assert resp.status_code == 201

    async def test_flowchart_returns_201(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/media/infographic",
                json={
                    "type": "flowchart",
                    "data": {
                        "title": "Process",
                        "nodes": [{"label": "Start"}, {"label": "Process"}, {"label": "End"}],
                    },
                },
            )
        assert resp.status_code == 201

    async def test_comparison_returns_201(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/media/infographic",
                json={
                    "type": "comparison",
                    "data": {
                        "title": "A vs B",
                        "left_label": "Option A",
                        "right_label": "Option B",
                        "left_items": ["Fast", "Cheap"],
                        "right_items": ["Slow", "Expensive"],
                    },
                },
            )
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Tests: GET /media/infographic-templates
# ---------------------------------------------------------------------------


class TestListInfographicTemplates:
    async def test_returns_five_builtin_templates(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/media/infographic-templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 5
        names = {t["name"] for t in data}
        assert "pie_chart" in names
        assert "bar_chart" in names
        assert "timeline" in names
        assert "flowchart" in names
        assert "comparison" in names

    async def test_template_has_required_fields(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/media/infographic-templates")
        item = resp.json()[0]
        for field in ("id", "name", "required_data_fields", "is_builtin"):
            assert field in item


# ---------------------------------------------------------------------------
# Tests: POST /media/icons/search
# ---------------------------------------------------------------------------


class TestSearchIcons:
    async def test_returns_200_with_icon_results(self) -> None:
        adapter = _make_search_adapter([{"url": "https://icons.com/star.svg", "source": "iconify"}])
        app = create_test_app(search_adapter=adapter)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/media/icons/search", json={"query": "star"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["type"] == "icon"

    async def test_icon_query_prefixed(self) -> None:
        adapter = _make_search_adapter([])
        app = create_test_app(search_adapter=adapter)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post("/media/icons/search", json={"query": "arrow"})
        adapter.search.assert_called_once_with("icon arrow", 10)
