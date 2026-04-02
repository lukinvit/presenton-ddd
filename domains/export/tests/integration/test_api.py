"""Integration tests for the Export API router."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from domains.export.api.router import create_export_router

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeJobRepo:
    def __init__(self) -> None:
        self._store: dict = {}

    async def get(self, job_id: object) -> object | None:
        return self._store.get(str(job_id))

    async def save(self, job: object) -> None:
        self._store[str(job.id)] = job  # type: ignore[attr-defined]

    async def list_by_presentation(self, presentation_id: object) -> list:
        return [j for j in self._store.values() if str(j.presentation_id) == str(presentation_id)]  # type: ignore[attr-defined]


def _make_pdf_exporter(output: str) -> AsyncMock:
    exporter = AsyncMock()
    exporter.export = AsyncMock(return_value=output)
    return exporter


def _make_pptx_exporter(output: str) -> AsyncMock:
    exporter = AsyncMock()
    exporter.export = AsyncMock(return_value=output)
    return exporter


def _make_app(pdf_exporter=None, pptx_exporter=None, repo=None) -> FastAPI:
    app = FastAPI()
    r = repo or FakeJobRepo()
    router = create_export_router(
        job_repo=r, pdf_exporter=pdf_exporter, pptx_exporter=pptx_exporter
    )
    app.include_router(router)
    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExportPDFEndpoint:
    async def test_returns_202_on_success(self) -> None:
        pdf = _make_pdf_exporter("/tmp/out.pdf")
        app = _make_app(pdf_exporter=pdf)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/export/pdf",
                json={"presentation_id": str(uuid.uuid4())},
            )
        assert resp.status_code == 202
        data = resp.json()
        assert data["format"] == "pdf"
        assert data["status"] == "completed"

    async def test_returns_503_when_no_exporter(self) -> None:
        app = _make_app()  # no pdf_exporter
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/export/pdf",
                json={"presentation_id": str(uuid.uuid4())},
            )
        assert resp.status_code == 503

    async def test_invalid_quality_returns_422(self) -> None:
        pdf = _make_pdf_exporter("/tmp/out.pdf")
        app = _make_app(pdf_exporter=pdf)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/export/pdf",
                json={"presentation_id": str(uuid.uuid4()), "quality": "ultra"},
            )
        assert resp.status_code == 422


class TestExportPPTXEndpoint:
    async def test_returns_202_on_success(self) -> None:
        pptx = _make_pptx_exporter("/tmp/out.pptx")
        app = _make_app(pptx_exporter=pptx)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/export/pptx",
                json={"presentation_id": str(uuid.uuid4())},
            )
        assert resp.status_code == 202
        data = resp.json()
        assert data["format"] == "pptx"
        assert data["status"] == "completed"

    async def test_returns_503_when_no_exporter(self) -> None:
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/export/pptx",
                json={"presentation_id": str(uuid.uuid4())},
            )
        assert resp.status_code == 503


class TestGetJobEndpoint:
    async def test_returns_404_for_unknown_job(self) -> None:
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get(f"/export/jobs/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_returns_job_after_creation(self) -> None:
        repo = FakeJobRepo()
        pdf = _make_pdf_exporter("/tmp/out.pdf")
        app = _make_app(pdf_exporter=pdf, repo=repo)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            create_resp = await c.post(
                "/export/pdf",
                json={"presentation_id": str(uuid.uuid4())},
            )
            assert create_resp.status_code == 202
            job_id = create_resp.json()["id"]

            get_resp = await c.get(f"/export/jobs/{job_id}")
            assert get_resp.status_code == 200
            assert get_resp.json()["id"] == job_id


class TestDownloadEndpoint:
    async def test_returns_404_when_file_missing(self) -> None:
        repo = FakeJobRepo()
        pdf = _make_pdf_exporter("/tmp/nonexistent_file_abc.pdf")
        app = _make_app(pdf_exporter=pdf, repo=repo)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            create_resp = await c.post(
                "/export/pdf",
                json={"presentation_id": str(uuid.uuid4())},
            )
            job_id = create_resp.json()["id"]
            dl_resp = await c.get(f"/export/jobs/{job_id}/download")
        assert dl_resp.status_code == 404


class TestListJobsEndpoint:
    async def test_returns_empty_list_for_unknown_presentation(self) -> None:
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get(f"/export/presentations/{uuid.uuid4()}/jobs")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_lists_jobs_by_presentation(self) -> None:
        repo = FakeJobRepo()
        pdf = _make_pdf_exporter("/tmp/out.pdf")
        app = _make_app(pdf_exporter=pdf, repo=repo)
        pres_id = str(uuid.uuid4())

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            await c.post("/export/pdf", json={"presentation_id": pres_id})
            await c.post("/export/pdf", json={"presentation_id": pres_id})
            resp = await c.get(f"/export/presentations/{pres_id}/jobs")

        assert resp.status_code == 200
        assert len(resp.json()) == 2
