from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from domains.auth.api.schemas import CallbackRequest, ConnectRequest, ConnectResponse
from domains.auth.application.commands import (
    HandleCallbackCommand,
    InitiateOAuthCommand,
    OAuthProviderAdapter,
)
from domains.auth.domain.repositories import OAuthConnectionRepository, OAuthStateRepository
from domains.auth.domain.services import EncryptionService
from shared.domain.events import EventBus


def create_auth_router(
    oauth_adapters: dict[str, OAuthProviderAdapter],
    state_repo: OAuthStateRepository,
    connection_repo: OAuthConnectionRepository,
    encryption_service: EncryptionService,
    event_bus: EventBus,
) -> APIRouter:
    router = APIRouter(tags=["auth"])

    @router.post("/connect", response_model=ConnectResponse)
    async def initiate_connect(req: ConnectRequest) -> ConnectResponse:
        adapter = oauth_adapters.get(req.provider)
        if adapter is None:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {req.provider}")
        cmd = InitiateOAuthCommand(oauth_provider_adapter=adapter, state_repo=state_repo)
        result = await cmd.execute(
            provider=req.provider, user_id=uuid.uuid4(), redirect_uri=req.redirect_uri
        )
        return ConnectResponse(authorize_url=result.authorize_url, state=result.state)

    @router.post("/callback")
    async def handle_callback(req: CallbackRequest) -> dict[str, str]:
        cmd = HandleCallbackCommand(
            oauth_provider_adapter=next(iter(oauth_adapters.values())),
            state_repo=state_repo,
            connection_repo=connection_repo,
            encryption_service=encryption_service,
            event_bus=event_bus,
        )
        try:
            await cmd.execute(code=req.code, state=req.state)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return {"status": "connected"}

    return router
