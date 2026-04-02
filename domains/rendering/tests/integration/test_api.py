"""Integration tests for the rendering FastAPI router."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from domains.rendering.api.router import create_rendering_router
from domains.rendering.domain.entities import RenderJob

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_html_renderer(html: str = "<div>rendered</div>") -> AsyncMock:
    renderer = AsyncMock()
    renderer.render = AsyncMock(return_value=html)
    return renderer


def _make_repo(jobs: list[RenderJob] | None = None) -> AsyncMock:
    store: dict[uuid.UUID, RenderJob] = {j.id: j for j in (jobs or [])}

    repo = AsyncMock()

    async def get(id: uuid.UUID) -> RenderJob | None:
        return store.get(id)

    async def save(job: RenderJob) -> None:
        store[job.id] = job

    async def list_all(limit: int = 50, offset: int = 0) -> list[RenderJob]:
        items = list(store.values())
        return items[offset : offset + limit]

    repo.get = AsyncMock(side_effect=get)
    repo.save = AsyncMock(side_effect=save)
    repo.list_all = AsyncMock(side_effect=list_all)
    return repo


def create_test_app(
    repo: AsyncMock | None = None,
    html: str = "<div>slide</div>",
) -> FastAPI:
    app = FastAPI()
    if repo is None:
        repo = _make_repo()
    renderer = _make_html_renderer(html)
    router = create_rendering_router(repo=repo, html_renderer=renderer)
    app.include_router(router)
    return app


# ---------------------------------------------------------------------------
# POST /rendering/slides
# ---------------------------------------------------------------------------


class TestRenderSlideEndpoint:
    async def test_render_slide_returns_201(self) -> None:
        app = create_test_app(html="<h1>Test</h1>")
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/rendering/slides",
                json={
                    "slide_id": str(uuid.uuid4()),
                    "slide_data": {"title": "Hello"},
                    "css_variables": "--color: red;",
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["html"] == "<h1>Test</h1>"
        assert "id" in data
        assert "slide_id" in data
        assert data["render_time_ms"] >= 0

    async def test_render_slide_with_config(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/rendering/slides",
                json={
                    "slide_id": str(uuid.uuid4()),
                    "slide_data": {},
                    "css_variables": "",
                    "config": {"width": 1280, "height": 720, "format": "html", "include_css": True},
                },
            )
        assert resp.status_code == 201


# ---------------------------------------------------------------------------
# POST /rendering/presentations/{id}
# ---------------------------------------------------------------------------


class TestRenderPresentationEndpoint:
    async def test_render_presentation_returns_201(self) -> None:
        app = create_test_app()
        presentation_id = uuid.uuid4()
        slide_id = uuid.uuid4()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/rendering/presentations/{presentation_id}",
                json={
                    "slides_data": [{"slide_id": str(slide_id), "data": {"title": "S1"}}],
                    "css_variables": "",
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["presentation_id"] == str(presentation_id)
        assert data["status"] == "completed"
        assert len(data["rendered_slides"]) == 1

    async def test_render_presentation_empty_slides(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/rendering/presentations/{uuid.uuid4()}",
                json={"slides_data": [], "css_variables": ""},
            )
        assert resp.status_code == 201
        assert resp.json()["status"] == "completed"
        assert resp.json()["rendered_slides"] == []


# ---------------------------------------------------------------------------
# POST /rendering/visual-diff
# ---------------------------------------------------------------------------


class TestVisualDiffEndpoint:
    async def test_diff_identical_images(self) -> None:
        app = create_test_app()
        slide_id = uuid.uuid4()
        img_hex = b"\x00\x01\x02".hex()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/rendering/visual-diff",
                json={"slide_id": str(slide_id), "image_a": img_hex, "image_b": img_hex},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["slide_id"] == str(slide_id)
        assert data["difference_percent"] == 0.0

    async def test_diff_different_images(self) -> None:
        app = create_test_app()
        slide_id = uuid.uuid4()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/rendering/visual-diff",
                json={
                    "slide_id": str(slide_id),
                    "image_a": b"\x00\x01".hex(),
                    "image_b": b"\xff\xfe".hex(),
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["difference_percent"] > 0.0


# ---------------------------------------------------------------------------
# GET /rendering/jobs/{id}
# ---------------------------------------------------------------------------


class TestGetRenderJobEndpoint:
    async def test_get_existing_job(self) -> None:
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        repo = _make_repo([job])
        app = create_test_app(repo=repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/rendering/jobs/{job.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(job.id)

    async def test_get_missing_job_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/rendering/jobs/{uuid.uuid4()}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /rendering/jobs/{id}/batch
# ---------------------------------------------------------------------------


class TestBatchRenderEndpoint:
    async def test_batch_render_existing_job(self) -> None:
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        repo = _make_repo([job])
        app = create_test_app(repo=repo)
        slide_id = uuid.uuid4()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/rendering/jobs/{job.id}/batch",
                json={
                    "slides_data": [{"slide_id": str(slide_id), "data": {}}],
                    "css_variables": "",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert len(data["rendered_slides"]) == 1

    async def test_batch_render_missing_job_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/rendering/jobs/{uuid.uuid4()}/batch",
                json={"slides_data": [], "css_variables": ""},
            )
        assert resp.status_code == 404
