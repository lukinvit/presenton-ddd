"""Unit tests for the Export MCP server tool registration."""

from __future__ import annotations

from domains.export.mcp.server import create_export_mcp_server


class TestExportMCPServer:
    def test_server_has_required_tools(self) -> None:
        server = create_export_mcp_server(
            job_repo=None,  # type: ignore[arg-type]
            pdf_exporter=None,
            pptx_exporter=None,
        )
        required_tools = [
            "export.to_pdf",
            "export.to_pptx",
            "export.status",
            "export.download",
            "health.check",
        ]
        for tool in required_tools:
            assert tool in server.registered_tools, f"Missing tool: {tool}"

    def test_server_name(self) -> None:
        server = create_export_mcp_server(job_repo=None, pdf_exporter=None, pptx_exporter=None)  # type: ignore[arg-type]
        assert server.name == "export"
