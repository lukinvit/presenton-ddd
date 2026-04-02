from domains.auth.mcp.server import create_auth_mcp_server


class TestAuthMCPServer:
    def test_server_has_required_tools(self) -> None:
        server = create_auth_mcp_server(
            oauth_adapters={},
            state_repo=None,
            connection_repo=None,
            encryption_service=None,
            event_bus=None,
        )
        required_tools = ["auth.connect", "auth.get_token", "auth.status", "health.check"]
        for tool in required_tools:
            assert tool in server.registered_tools, f"Missing tool: {tool}"
