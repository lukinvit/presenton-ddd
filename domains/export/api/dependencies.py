"""FastAPI dependency injection helpers for the export domain."""

from __future__ import annotations

from domains.export.domain.repositories import ExportJobRepository
from domains.export.domain.services import PDFExporter, PPTXExporter

# ---------------------------------------------------------------------------
# In-memory stub implementations used as defaults (replace in production)
# ---------------------------------------------------------------------------


class InMemoryExportJobRepository:
    """Simple dict-backed repository for testing / local dev."""

    def __init__(self) -> None:
        self._store: dict = {}

    async def get(self, job_id: object) -> object | None:
        return self._store.get(str(job_id))

    async def save(self, job: object) -> None:
        self._store[str(job.id)] = job  # type: ignore[attr-defined]

    async def list_by_presentation(self, presentation_id: object) -> list:
        return [j for j in self._store.values() if str(j.presentation_id) == str(presentation_id)]  # type: ignore[attr-defined]


# Module-level singletons (overridable via app.dependency_overrides)
_job_repo: ExportJobRepository = InMemoryExportJobRepository()  # type: ignore[assignment]
_pdf_exporter: PDFExporter | None = None
_pptx_exporter: PPTXExporter | None = None


def get_job_repo() -> ExportJobRepository:
    return _job_repo


def get_pdf_exporter() -> PDFExporter:
    if _pdf_exporter is None:
        raise RuntimeError("PDFExporter has not been configured")
    return _pdf_exporter


def get_pptx_exporter() -> PPTXExporter:
    if _pptx_exporter is None:
        raise RuntimeError("PPTXExporter has not been configured")
    return _pptx_exporter


def configure_exporters(
    pdf: PDFExporter | None = None,
    pptx: PPTXExporter | None = None,
) -> None:
    """Wire real exporters at application startup."""
    global _pdf_exporter, _pptx_exporter
    if pdf is not None:
        _pdf_exporter = pdf
    if pptx is not None:
        _pptx_exporter = pptx
