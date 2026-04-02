"""Export MCP server."""

from __future__ import annotations

import uuid

from domains.export.domain.repositories import ExportJobRepository
from domains.export.domain.services import PDFExporter, PPTXExporter
from domains.export.domain.value_objects import ExportConfig, ExportFormat
from shared.mcp.server_base import DomainMCPServer


def create_export_mcp_server(
    job_repo: ExportJobRepository,
    pdf_exporter: PDFExporter | None,
    pptx_exporter: PPTXExporter | None,
) -> DomainMCPServer:
    server = DomainMCPServer(name="export", port=9084)

    @server.tool("export.to_pdf")
    async def to_pdf(
        presentation_id: str,
        include_speaker_notes: bool = False,
        quality: str = "high",
    ) -> dict:
        from domains.export.application.commands import ExportToPDFCommand

        if pdf_exporter is None:
            return {"error": "PDF exporter not configured"}
        config = ExportConfig(
            format=ExportFormat.PDF,
            include_speaker_notes=include_speaker_notes,
            quality=quality,
        )
        cmd = ExportToPDFCommand(job_repo=job_repo, pdf_exporter=pdf_exporter)
        pres_id = uuid.UUID(presentation_id)
        dto = await cmd.execute(
            presentation_id=pres_id,
            config=config,
            html_slides=[],
            output_path=f"/tmp/export_{pres_id}.pdf",
        )
        return {
            "job_id": dto.id,
            "status": dto.status,
            "output_path": dto.output_path,
        }

    @server.tool("export.to_pptx")
    async def to_pptx(
        presentation_id: str,
        include_speaker_notes: bool = False,
        quality: str = "high",
    ) -> dict:
        from domains.export.application.commands import ExportToPPTXCommand

        if pptx_exporter is None:
            return {"error": "PPTX exporter not configured"}
        config = ExportConfig(
            format=ExportFormat.PPTX,
            include_speaker_notes=include_speaker_notes,
            quality=quality,
        )
        cmd = ExportToPPTXCommand(job_repo=job_repo, pptx_exporter=pptx_exporter)
        pres_id = uuid.UUID(presentation_id)
        dto = await cmd.execute(
            presentation_id=pres_id,
            config=config,
            slides_data=[],
            style_data={},
            output_path=f"/tmp/export_{pres_id}.pptx",
        )
        return {
            "job_id": dto.id,
            "status": dto.status,
            "output_path": dto.output_path,
        }

    @server.tool("export.status")
    async def status(job_id: str) -> dict:
        from domains.export.application.commands import CheckExportStatusCommand

        cmd = CheckExportStatusCommand(job_repo=job_repo)
        try:
            dto = await cmd.execute(uuid.UUID(job_id))
        except ValueError as exc:
            return {"error": str(exc)}
        return {
            "job_id": dto.id,
            "status": dto.status,
            "output_path": dto.output_path,
            "error_message": dto.error_message,
        }

    @server.tool("export.download")
    async def download(job_id: str) -> dict:
        from domains.export.application.queries import GetExportJobQuery

        query = GetExportJobQuery(job_repo=job_repo)
        try:
            dto = await query.execute(uuid.UUID(job_id))
        except ValueError as exc:
            return {"error": str(exc)}
        if dto.output_path is None:
            return {"error": "No output file available"}
        return {"output_path": dto.output_path, "format": dto.format}

    return server
