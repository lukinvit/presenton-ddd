"""Export API router."""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from domains.export.api.schemas import ExportJobResponse, ExportRequest
from domains.export.application.commands import (
    ExportToPDFCommand,
    ExportToPPTXCommand,
)
from domains.export.application.queries import GetExportJobQuery, ListExportJobsQuery
from domains.export.domain.repositories import ExportJobRepository
from domains.export.domain.services import PDFExporter, PPTXExporter
from domains.export.domain.value_objects import ExportConfig, ExportFormat


def _dto_to_response(dto: object) -> ExportJobResponse:
    from domains.export.application.dto import ExportJobDTO

    assert isinstance(dto, ExportJobDTO)
    return ExportJobResponse(
        id=dto.id,
        presentation_id=dto.presentation_id,
        format=dto.format,
        status=dto.status,
        output_path=dto.output_path,
        error_message=dto.error_message,
        created_at=dto.created_at,
        completed_at=dto.completed_at,
    )


def create_export_router(
    job_repo: ExportJobRepository,
    pdf_exporter: PDFExporter | None = None,
    pptx_exporter: PPTXExporter | None = None,
) -> APIRouter:
    router = APIRouter(tags=["export"])

    # ------------------------------------------------------------------
    # POST /export/pdf
    # ------------------------------------------------------------------
    @router.post("/export/pdf", response_model=ExportJobResponse, status_code=202)
    async def export_to_pdf(req: ExportRequest) -> ExportJobResponse:
        if pdf_exporter is None:
            raise HTTPException(status_code=503, detail="PDF exporter not configured")
        config = ExportConfig(
            format=ExportFormat.PDF,
            include_speaker_notes=req.include_speaker_notes,
            quality=req.quality,
        )
        # In a real system html_slides would come from the presentation domain.
        # For now we accept a minimal invocation.
        cmd = ExportToPDFCommand(job_repo=job_repo, pdf_exporter=pdf_exporter)
        try:
            pres_id = uuid.UUID(req.presentation_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid presentation_id") from exc
        dto = await cmd.execute(
            presentation_id=pres_id,
            config=config,
            html_slides=[],
            output_path=f"/tmp/export_{pres_id}.pdf",
        )
        return _dto_to_response(dto)

    # ------------------------------------------------------------------
    # POST /export/pptx
    # ------------------------------------------------------------------
    @router.post("/export/pptx", response_model=ExportJobResponse, status_code=202)
    async def export_to_pptx(req: ExportRequest) -> ExportJobResponse:
        if pptx_exporter is None:
            raise HTTPException(status_code=503, detail="PPTX exporter not configured")
        config = ExportConfig(
            format=ExportFormat.PPTX,
            include_speaker_notes=req.include_speaker_notes,
            quality=req.quality,
        )
        cmd = ExportToPPTXCommand(job_repo=job_repo, pptx_exporter=pptx_exporter)
        try:
            pres_id = uuid.UUID(req.presentation_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid presentation_id") from exc
        dto = await cmd.execute(
            presentation_id=pres_id,
            config=config,
            slides_data=[],
            style_data={},
            output_path=f"/tmp/export_{pres_id}.pptx",
        )
        return _dto_to_response(dto)

    # ------------------------------------------------------------------
    # GET /export/jobs/{id}
    # ------------------------------------------------------------------
    @router.get("/export/jobs/{job_id}", response_model=ExportJobResponse)
    async def get_job(job_id: str) -> ExportJobResponse:
        try:
            jid = uuid.UUID(job_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid job_id") from exc
        query = GetExportJobQuery(job_repo=job_repo)
        try:
            dto = await query.execute(jid)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _dto_to_response(dto)

    # ------------------------------------------------------------------
    # GET /export/jobs/{id}/download
    # ------------------------------------------------------------------
    @router.get("/export/jobs/{job_id}/download")
    async def download_job(job_id: str) -> FileResponse:
        try:
            jid = uuid.UUID(job_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid job_id") from exc
        query = GetExportJobQuery(job_repo=job_repo)
        try:
            dto = await query.execute(jid)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        if dto.output_path is None or not os.path.exists(dto.output_path):
            raise HTTPException(status_code=404, detail="File not found")

        media_type = (
            "application/pdf"
            if dto.format == "pdf"
            else ("application/vnd.openxmlformats-officedocument.presentationml.presentation")
        )
        return FileResponse(path=dto.output_path, media_type=media_type)

    # ------------------------------------------------------------------
    # GET /export/presentations/{presentation_id}/jobs
    # ------------------------------------------------------------------
    @router.get(
        "/export/presentations/{presentation_id}/jobs",
        response_model=list[ExportJobResponse],
    )
    async def list_jobs(presentation_id: str) -> list[ExportJobResponse]:
        try:
            pres_id = uuid.UUID(presentation_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail="Invalid presentation_id") from exc
        query = ListExportJobsQuery(job_repo=job_repo)
        dtos = await query.execute(pres_id)
        return [_dto_to_response(d) for d in dtos]

    return router
