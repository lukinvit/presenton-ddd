from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from domains.auth.application.dto import OAuthURLDTO
from domains.auth.domain.entities import OAuthConnection
from domains.auth.domain.repositories import OAuthConnectionRepository, OAuthStateRepository
from domains.auth.domain.services import EncryptionService
from domains.auth.domain.value_objects import EncryptedToken, OAuthProvider
from shared.domain.events import DomainEvent, EventBus


class OAuthProviderAdapter(Protocol):
    async def get_authorize_url(self, redirect_uri: str) -> tuple[str, str, str]: ...
    async def exchange_code(
        self, code: str, code_verifier: str, redirect_uri: str
    ) -> dict[str, Any]: ...


@dataclass
class InitiateOAuthCommand:
    oauth_provider_adapter: OAuthProviderAdapter
    state_repo: OAuthStateRepository

    async def execute(self, provider: str, user_id: uuid.UUID, redirect_uri: str) -> OAuthURLDTO:
        authorize_url, state, code_verifier = await self.oauth_provider_adapter.get_authorize_url(
            redirect_uri
        )
        await self.state_repo.save(
            state, {"provider": provider, "user_id": str(user_id), "code_verifier": code_verifier}
        )
        return OAuthURLDTO(authorize_url=authorize_url, state=state)


@dataclass
class HandleCallbackCommand:
    oauth_provider_adapter: OAuthProviderAdapter
    state_repo: OAuthStateRepository
    connection_repo: OAuthConnectionRepository
    encryption_service: EncryptionService
    event_bus: EventBus

    async def execute(self, code: str, state: str) -> None:
        state_data = await self.state_repo.get_and_delete(state)
        if state_data is None:
            raise ValueError("Invalid or expired OAuth state")
        tokens = await self.oauth_provider_adapter.exchange_code(
            code=code,
            code_verifier=state_data["code_verifier"],
            redirect_uri="",
        )
        provider = OAuthProvider(state_data["provider"])
        user_id = uuid.UUID(state_data["user_id"])
        expires_at = None
        if tokens.get("expires_in"):
            expires_at = datetime.now(UTC) + timedelta(seconds=tokens["expires_in"])
        connection = OAuthConnection(
            id=uuid.uuid4(),
            user_id=user_id,
            provider=provider,
            access_token=EncryptedToken(
                value=self.encryption_service.encrypt(tokens["access_token"])
            ),
            refresh_token=EncryptedToken(
                value=self.encryption_service.encrypt(tokens["refresh_token"])
            )
            if tokens.get("refresh_token")
            else None,
            expires_at=expires_at,
        )
        await self.connection_repo.save(connection)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=connection.id,
                event_type="ProviderConnected",
                payload={"user_id": str(user_id), "provider": provider.value},
            )
        )
