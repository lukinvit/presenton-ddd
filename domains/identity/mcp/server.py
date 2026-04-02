from __future__ import annotations

from domains.identity.domain.repositories import UserRepository
from domains.identity.domain.services import TokenService
from shared.domain.events import EventBus
from shared.mcp.server_base import DomainMCPServer


def create_identity_mcp_server(
    user_repo: UserRepository,
    event_bus: EventBus,
    token_service: TokenService,
) -> DomainMCPServer:
    server = DomainMCPServer(name="identity", port=9080)

    @server.tool("identity.register")
    async def register(email: str, password: str) -> dict:
        from domains.identity.application.commands import RegisterUserCommand

        cmd = RegisterUserCommand(
            user_repo=user_repo, event_bus=event_bus, token_service=token_service
        )
        result = await cmd.execute(email=email, password=password)
        return {"access_token": result.access_token, "refresh_token": result.refresh_token}

    @server.tool("identity.login")
    async def login(email: str, password: str) -> dict:
        from domains.identity.application.commands import LoginUserCommand

        cmd = LoginUserCommand(
            user_repo=user_repo, event_bus=event_bus, token_service=token_service
        )
        result = await cmd.execute(email=email, password=password)
        return {"access_token": result.access_token, "refresh_token": result.refresh_token}

    @server.tool("identity.verify_session")
    async def verify_session(token: str) -> dict:
        payload = token_service.verify_token(token)
        return {"user_id": payload["sub"], "roles": payload.get("roles", [])}

    return server
