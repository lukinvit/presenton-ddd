from __future__ import annotations

import uuid

from shared.domain.events import EventBus
from shared.mcp.server_base import DomainMCPServer

from domains.auth.application.commands import InitiateOAuthCommand, OAuthProviderAdapter
from domains.auth.application.queries import GetConnectionStatusQuery, GetTokenQuery
from domains.auth.domain.repositories import OAuthConnectionRepository, OAuthStateRepository
from domains.auth.domain.services import EncryptionService


def create_auth_mcp_server(
    oauth_adapters: dict[str, OAuthProviderAdapter],
    state_repo: OAuthStateRepository,
    connection_repo: OAuthConnectionRepository,
    encryption_service: EncryptionService,
    event_bus: EventBus,
) -> DomainMCPServer:
    server = DomainMCPServer(name="auth", port=9070)

    @server.tool("auth.connect")
    async def connect(provider: str, user_id: str, redirect_uri: str) -> dict:
        adapter = oauth_adapters.get(provider)
        if adapter is None:
            return {"error": f"Unknown provider: {provider}"}
        cmd = InitiateOAuthCommand(oauth_provider_adapter=adapter, state_repo=state_repo)
        result = await cmd.execute(provider=provider, user_id=uuid.UUID(user_id), redirect_uri=redirect_uri)
        return {"authorize_url": result.authorize_url, "state": result.state}

    @server.tool("auth.get_token")
    async def get_token(user_id: str, provider: str) -> dict:
        query = GetTokenQuery(connection_repo=connection_repo, encryption_service=encryption_service)
        token = await query.execute(user_id=uuid.UUID(user_id), provider=provider)
        return {"access_token": token}

    @server.tool("auth.status")
    async def status(user_id: str) -> dict:
        query = GetConnectionStatusQuery(connection_repo=connection_repo)
        statuses = await query.execute(user_id=uuid.UUID(user_id))
        return {"connections": [{"provider": s.provider, "connected": s.connected} for s in statuses]}

    return server
