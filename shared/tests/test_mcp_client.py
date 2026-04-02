import pytest

from shared.mcp.client import MCPClient, MCPToolCall


class TestMCPClient:
    def test_create_client(self) -> None:
        client = MCPClient(
            base_urls={
                "presentation": "http://localhost:9010",
                "style": "http://localhost:9020",
            }
        )
        assert "presentation" in client.base_urls
        assert "style" in client.base_urls

    def test_resolve_domain_from_tool_name(self) -> None:
        client = MCPClient(
            base_urls={
                "presentation": "http://localhost:9010",
                "style": "http://localhost:9020",
            }
        )
        assert client._resolve_domain("presentation.create") == "presentation"
        assert client._resolve_domain("style.extract_from_file") == "style"

    def test_resolve_domain_unknown_raises(self) -> None:
        client = MCPClient(
            base_urls={
                "presentation": "http://localhost:9010",
            }
        )
        with pytest.raises(ValueError, match="Unknown domain"):
            client._resolve_domain("unknown.tool")


class TestMCPToolCall:
    def test_tool_call_dataclass(self) -> None:
        call = MCPToolCall(tool="presentation.create", arguments={"title": "Test"})
        assert call.tool == "presentation.create"
        assert call.arguments == {"title": "Test"}
