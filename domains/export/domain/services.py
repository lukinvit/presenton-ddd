"""Export domain service protocols (infrastructure adapters)."""

from __future__ import annotations

from typing import Protocol

from .value_objects import ExportConfig


class PDFExporter(Protocol):
    """Export HTML slides to PDF via Puppeteer."""

    async def export(
        self,
        html_slides: list[str],
        output_path: str,
        config: ExportConfig,
    ) -> str: ...


class PPTXExporter(Protocol):
    """Export slide data to PPTX via python-pptx."""

    async def export(
        self,
        slides_data: list[dict],
        style_data: dict,
        output_path: str,
        config: ExportConfig,
    ) -> str: ...
