"""Unit tests for ExportJob entity."""

from __future__ import annotations

import uuid

from domains.export.domain.entities import ExportJob
from domains.export.domain.value_objects import ExportFormat, ExportStatus


class TestExportJobEntity:
    def test_initial_status_is_pending(self) -> None:
        job = ExportJob(id=uuid.uuid4(), presentation_id=uuid.uuid4(), format=ExportFormat.PDF)
        assert job.status == ExportStatus.PENDING

    def test_mark_processing(self) -> None:
        job = ExportJob(id=uuid.uuid4(), presentation_id=uuid.uuid4(), format=ExportFormat.PDF)
        job.mark_processing()
        assert job.status == ExportStatus.PROCESSING

    def test_mark_completed_sets_path_and_time(self) -> None:
        job = ExportJob(id=uuid.uuid4(), presentation_id=uuid.uuid4(), format=ExportFormat.PDF)
        job.mark_completed("/tmp/out.pdf")
        assert job.status == ExportStatus.COMPLETED
        assert job.output_path == "/tmp/out.pdf"
        assert job.completed_at is not None

    def test_mark_failed_sets_error_and_time(self) -> None:
        job = ExportJob(id=uuid.uuid4(), presentation_id=uuid.uuid4(), format=ExportFormat.PPTX)
        job.mark_failed("Renderer crashed")
        assert job.status == ExportStatus.FAILED
        assert job.error_message == "Renderer crashed"
        assert job.completed_at is not None

    def test_equality_by_id(self) -> None:
        jid = uuid.uuid4()
        j1 = ExportJob(id=jid, presentation_id=uuid.uuid4(), format=ExportFormat.PDF)
        j2 = ExportJob(id=jid, presentation_id=uuid.uuid4(), format=ExportFormat.PPTX)
        assert j1 == j2
