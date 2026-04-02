from domains.identity.mcp.server import create_identity_mcp_server


class TestIdentityMCPServer:
    def test_server_has_required_tools(self) -> None:
        server = create_identity_mcp_server(user_repo=None, event_bus=None, token_service=None)
        required_tools = [
            "identity.register",
            "identity.login",
            "identity.verify_session",
            "health.check",
        ]
        for tool in required_tools:
            assert tool in server.registered_tools, f"Missing tool: {tool}"
