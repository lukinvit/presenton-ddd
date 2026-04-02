import pytest
from shared.mcp.server_base import DomainMCPServer

class TestDomainMCPServer:
    def test_create_server_with_name(self) -> None:
        server = DomainMCPServer(name="presentation", port=9010)
        assert server.name == "presentation"
        assert server.port == 9010

    def test_server_has_mcp_app(self) -> None:
        server = DomainMCPServer(name="style", port=9020)
        assert server.mcp is not None

    def test_register_tool(self) -> None:
        server = DomainMCPServer(name="test", port=9999)
        @server.tool("test.echo")
        async def echo(message: str) -> str:
            return message
        assert "test.echo" in server.registered_tools

    def test_health_endpoint_registered(self) -> None:
        server = DomainMCPServer(name="test", port=9999)
        assert "health.check" in server.registered_tools
