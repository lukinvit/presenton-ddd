"""Integration tests for the presentation FastAPI router."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from domains.presentation.api.router import create_presentation_router
from domains.presentation.domain.entities import Presentation, Slide


def _make_repo(presentations: list[Presentation] | None = None) -> AsyncMock:
    store: dict[uuid.UUID, Presentation] = {p.id: p for p in (presentations or [])}

    repo = AsyncMock()

    async def get(id: uuid.UUID) -> Presentation | None:
        return store.get(id)

    async def save(presentation: Presentation) -> None:
        store[presentation.id] = presentation

    async def delete(id: uuid.UUID) -> None:
        store.pop(id, None)

    async def list_all(limit: int = 50, offset: int = 0) -> list[Presentation]:
        items = list(store.values())
        return items[offset : offset + limit]

    repo.get = AsyncMock(side_effect=get)
    repo.save = AsyncMock(side_effect=save)
    repo.delete = AsyncMock(side_effect=delete)
    repo.list_all = AsyncMock(side_effect=list_all)
    return repo


def create_test_app(repo: AsyncMock | None = None) -> FastAPI:
    app = FastAPI()
    if repo is None:
        repo = _make_repo()
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock()
    router = create_presentation_router(repo=repo, event_bus=event_bus)
    app.include_router(router)
    return app


class TestCreatePresentation:
    async def test_create_returns_201(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/presentations", json={"title": "My Deck", "description": "Desc"}
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "My Deck"
        assert data["status"] == "draft"
        assert "id" in data

    async def test_create_empty_title_returns_422(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/presentations", json={"title": ""})
        assert resp.status_code == 422


class TestGetPresentation:
    async def test_get_existing_presentation(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Existing", description="")
        repo = _make_repo([p])
        app = create_test_app(repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/presentations/{p.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(p.id)

    async def test_get_missing_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/presentations/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestListPresentations:
    async def test_list_empty(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/presentations")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_with_items(self) -> None:
        p1 = Presentation(id=uuid.uuid4(), title="P1", description="")
        p2 = Presentation(id=uuid.uuid4(), title="P2", description="")
        repo = _make_repo([p1, p2])
        app = create_test_app(repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/presentations")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


class TestUpdatePresentation:
    async def test_update_title(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Old", description="")
        repo = _make_repo([p])
        app = create_test_app(repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(f"/presentations/{p.id}", json={"title": "New"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "New"

    async def test_update_missing_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(f"/presentations/{uuid.uuid4()}", json={"title": "X"})
        assert resp.status_code == 404


class TestDeletePresentation:
    async def test_delete_existing(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="ToDelete", description="")
        repo = _make_repo([p])
        app = create_test_app(repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/presentations/{p.id}")
        assert resp.status_code == 204

    async def test_delete_missing_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/presentations/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestSlideEndpoints:
    async def test_add_slide(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        repo = _make_repo([p])
        app = create_test_app(repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/presentations/{p.id}/slides",
                json={"title": "Intro", "layout_type": "title"},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Intro"
        assert data["index"] == 0

    async def test_add_slide_to_missing_presentation(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/presentations/{uuid.uuid4()}/slides",
                json={"title": "Slide"},
            )
        assert resp.status_code == 404

    async def test_update_slide(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        s = Slide(id=uuid.uuid4(), presentation_id=p.id, title="Old")
        p.add_slide(s)
        repo = _make_repo([p])
        app = create_test_app(repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(f"/presentations/{p.id}/slides/{s.id}", json={"title": "New"})
        assert resp.status_code == 200
        assert resp.json()["title"] == "New"

    async def test_delete_slide(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        s = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S")
        p.add_slide(s)
        repo = _make_repo([p])
        app = create_test_app(repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(f"/presentations/{p.id}/slides/{s.id}")
        assert resp.status_code == 204

    async def test_reorder_slides(self) -> None:
        p = Presentation(id=uuid.uuid4(), title="Deck", description="")
        s1 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S1")
        s2 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S2")
        p.add_slide(s1)
        p.add_slide(s2)
        repo = _make_repo([p])
        app = create_test_app(repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.put(
                f"/presentations/{p.id}/slides/reorder",
                json={"slide_ids": [str(s2.id), str(s1.id)]},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
