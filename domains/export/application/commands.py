"""Export application commands."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from domains.export.application.dto import ExportJobDTO
from domains.export.domain.entities import ExportJob
from domains.export.domain.repositories import ExportJobRepository
from domains.export.domain.services import PDFExporter, PPTXExporter
from domains.export.domain.value_objects import ExportConfig, ExportFormat, ExportStatus


@dataclass
class ExportToPDFCommand:
    """Create an export job and run the PDF exporter."""

    job_repo: ExportJobRepository
    pdf_exporter: PDFExporter

    async def execute(
        self,
        presentation_id: uuid.UUID,
        config: ExportConfig,
        html_slides: list[str],
        output_path: str,
    ) -> ExportJobDTO:
        job = ExportJob(
            id=uuid.uuid4(),
            presentation_id=presentation_id,
            format=ExportFormat.PDF,
            status=ExportStatus.PENDING,
        )
        await self.job_repo.save(job)

        job.mark_processing()
        await self.job_repo.save(job)

        try:
            result_path = await self.pdf_exporter.export(
                html_slides=html_slides,
                output_path=output_path,
                config=config,
            )
            job.mark_completed(result_path)
        except Exception as exc:
            job.mark_failed(str(exc))
        finally:
            await self.job_repo.save(job)

        return ExportJobDTO.from_entity(job)


@dataclass
class ExportToPPTXCommand:
    """Create an export job and run the PPTX exporter."""

    job_repo: ExportJobRepository
    pptx_exporter: PPTXExporter

    async def execute(
        self,
        presentation_id: uuid.UUID,
        config: ExportConfig,
        slides_data: list[dict],
        style_data: dict,
        output_path: str,
    ) -> ExportJobDTO:
        job = ExportJob(
            id=uuid.uuid4(),
            presentation_id=presentation_id,
            format=ExportFormat.PPTX,
            status=ExportStatus.PENDING,
        )
        await self.job_repo.save(job)

        job.mark_processing()
        await self.job_repo.save(job)

        try:
            result_path = await self.pptx_exporter.export(
                slides_data=slides_data,
                style_data=style_data,
                output_path=output_path,
                config=config,
            )
            job.mark_completed(result_path)
        except Exception as exc:
            job.mark_failed(str(exc))
        finally:
            await self.job_repo.save(job)

        return ExportJobDTO.from_entity(job)


@dataclass
class CheckExportStatusCommand:
    """Fetch the current status of an export job."""

    job_repo: ExportJobRepository

    async def execute(self, job_id: uuid.UUID) -> ExportJobDTO:
        job = await self.job_repo.get(job_id)
        if job is None:
            raise ValueError(f"Export job '{job_id}' not found")
        return ExportJobDTO.from_entity(job)
