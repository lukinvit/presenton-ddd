"""Unit tests for Export commands (PDFExporter and PPTXExporter are mocked)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from domains.export.application.commands import (
    CheckExportStatusCommand,
    ExportToPDFCommand,
    ExportToPPTXCommand,
)
from domains.export.application.dto import ExportJobDTO
from domains.export.domain.entities import ExportJob
from domains.export.domain.value_objects import ExportConfig, ExportFormat, ExportStatus


def _make_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.get = AsyncMock(return_value=None)
    repo.list_by_presentation = AsyncMock(return_value=[])
    return repo


class TestExportToPDFCommand:
    async def test_success_returns_completed_dto(self) -> None:
        repo = _make_repo()
        pdf_exporter = AsyncMock()
        pdf_exporter.export = AsyncMock(return_value="/tmp/out.pdf")

        cmd = ExportToPDFCommand(job_repo=repo, pdf_exporter=pdf_exporter)
        config = ExportConfig(format=ExportFormat.PDF)
        dto = await cmd.execute(
            presentation_id=uuid.uuid4(),
            config=config,
            html_slides=["<html/>"],
            output_path="/tmp/out.pdf",
        )

        assert isinstance(dto, ExportJobDTO)
        assert dto.status == "completed"
        assert dto.output_path == "/tmp/out.pdf"
        assert dto.format == "pdf"
        # save called at least 3 times: PENDING, PROCESSING, final
        assert repo.save.call_count >= 3

    async def test_exporter_error_marks_job_failed(self) -> None:
        repo = _make_repo()
        pdf_exporter = AsyncMock()
        pdf_exporter.export = AsyncMock(side_effect=RuntimeError("Puppeteer failed"))

        cmd = ExportToPDFCommand(job_repo=repo, pdf_exporter=pdf_exporter)
        config = ExportConfig(format=ExportFormat.PDF)
        dto = await cmd.execute(
            presentation_id=uuid.uuid4(),
            config=config,
            html_slides=[],
            output_path="/tmp/out.pdf",
        )

        assert dto.status == "failed"
        assert "Puppeteer failed" in (dto.error_message or "")

    async def test_creates_job_with_pending_then_processing(self) -> None:
        statuses: list[str] = []

        async def capture_save(job: object) -> None:
            from domains.export.domain.entities import ExportJob as EJ

            assert isinstance(job, EJ)
            statuses.append(job.status.value)

        repo = _make_repo()
        repo.save = capture_save

        pdf_exporter = AsyncMock()
        pdf_exporter.export = AsyncMock(return_value="/tmp/out.pdf")

        cmd = ExportToPDFCommand(job_repo=repo, pdf_exporter=pdf_exporter)
        await cmd.execute(
            presentation_id=uuid.uuid4(),
            config=ExportConfig(format=ExportFormat.PDF),
            html_slides=[],
            output_path="/tmp/out.pdf",
        )

        assert statuses[0] == "pending"
        assert statuses[1] == "processing"
        assert statuses[-1] == "completed"


class TestExportToPPTXCommand:
    async def test_success_returns_completed_dto(self) -> None:
        repo = _make_repo()
        pptx_exporter = AsyncMock()
        pptx_exporter.export = AsyncMock(return_value="/tmp/out.pptx")

        cmd = ExportToPPTXCommand(job_repo=repo, pptx_exporter=pptx_exporter)
        config = ExportConfig(format=ExportFormat.PPTX)
        dto = await cmd.execute(
            presentation_id=uuid.uuid4(),
            config=config,
            slides_data=[{"title": "Slide 1"}],
            style_data={"color": "blue"},
            output_path="/tmp/out.pptx",
        )

        assert dto.status == "completed"
        assert dto.format == "pptx"
        assert dto.output_path == "/tmp/out.pptx"

    async def test_exporter_error_marks_job_failed(self) -> None:
        repo = _make_repo()
        pptx_exporter = AsyncMock()
        pptx_exporter.export = AsyncMock(side_effect=RuntimeError("python-pptx error"))

        cmd = ExportToPPTXCommand(job_repo=repo, pptx_exporter=pptx_exporter)
        dto = await cmd.execute(
            presentation_id=uuid.uuid4(),
            config=ExportConfig(format=ExportFormat.PPTX),
            slides_data=[],
            style_data={},
            output_path="/tmp/out.pptx",
        )

        assert dto.status == "failed"
        assert "python-pptx error" in (dto.error_message or "")


class TestCheckExportStatusCommand:
    async def test_returns_dto_for_existing_job(self) -> None:
        jid = uuid.uuid4()
        existing = ExportJob(
            id=jid,
            presentation_id=uuid.uuid4(),
            format=ExportFormat.PDF,
            status=ExportStatus.COMPLETED,
        )
        existing.mark_completed("/tmp/out.pdf")
        repo = _make_repo()
        repo.get = AsyncMock(return_value=existing)

        cmd = CheckExportStatusCommand(job_repo=repo)
        dto = await cmd.execute(jid)
        assert dto.id == str(jid)
        assert dto.status == "completed"

    async def test_raises_for_missing_job(self) -> None:
        repo = _make_repo()
        repo.get = AsyncMock(return_value=None)

        cmd = CheckExportStatusCommand(job_repo=repo)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(uuid.uuid4())
