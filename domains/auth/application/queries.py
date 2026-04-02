from __future__ import annotations
import uuid
from dataclasses import dataclass
from domain.repositories import OAuthConnectionRepository
from domain.services import EncryptionService
from domain.value_objects import OAuthProvider
from application.dto import ConnectionStatusDTO


@dataclass
class GetTokenQuery:
    connection_repo: OAuthConnectionRepository
    encryption_service: EncryptionService

    async def execute(self, user_id: uuid.UUID, provider: str) -> str:
        oauth_provider = OAuthProvider(provider)
        conn = await self.connection_repo.get_by_user_and_provider(user_id, oauth_provider)
        if conn is None:
            raise ValueError(f"No connection for provider '{provider}'")
        return self.encryption_service.decrypt(conn.access_token.value)


@dataclass
class GetConnectionStatusQuery:
    connection_repo: OAuthConnectionRepository

    async def execute(self, user_id: uuid.UUID) -> list[ConnectionStatusDTO]:
        statuses = []
        for provider in OAuthProvider:
            conn = await self.connection_repo.get_by_user_and_provider(user_id, provider)
            statuses.append(ConnectionStatusDTO(
                provider=provider.value,
                connected=conn is not None,
                expires_at=conn.expires_at.isoformat() if conn and conn.expires_at else None,
            ))
        return statuses
