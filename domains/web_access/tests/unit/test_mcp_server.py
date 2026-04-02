from __future__ import annotations

from domains.web_access.mcp.server import create_web_access_mcp_server


class TestWebAccessMCPServer:
    def test_server_has_required_tools(self) -> None:
        server = create_web_access_mcp_server(
            search_adapter=None,  # type: ignore[arg-type]
            fetch_adapter=None,  # type: ignore[arg-type]
            screenshot_adapter=None,  # type: ignore[arg-type]
            query_repo=None,  # type: ignore[arg-type]
            event_bus=None,  # type: ignore[arg-type]
        )
        required_tools = [
            "web.search",
            "web.fetch",
            "web.screenshot",
            "web.extract_data",
            "health.check",
        ]
        for tool in required_tools:
            assert tool in server.registered_tools, f"Missing tool: {tool}"

    def test_server_name(self) -> None:
        server = create_web_access_mcp_server(
            search_adapter=None,  # type: ignore[arg-type]
            fetch_adapter=None,  # type: ignore[arg-type]
            screenshot_adapter=None,  # type: ignore[arg-type]
            query_repo=None,  # type: ignore[arg-type]
            event_bus=None,  # type: ignore[arg-type]
        )
        assert server.name == "web_access"

    def test_server_port(self) -> None:
        server = create_web_access_mcp_server(
            search_adapter=None,  # type: ignore[arg-type]
            fetch_adapter=None,  # type: ignore[arg-type]
            screenshot_adapter=None,  # type: ignore[arg-type]
            query_repo=None,  # type: ignore[arg-type]
            event_bus=None,  # type: ignore[arg-type]
        )
        assert server.port == 9071
