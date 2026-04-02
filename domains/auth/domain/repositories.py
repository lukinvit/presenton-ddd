from __future__ import annotations

import uuid
from typing import Any, Protocol

from .entities import OAuthConnection
from .value_objects import OAuthProvider


class OAuthConnectionRepository(Protocol):
    async def get(self, id: uuid.UUID) -> OAuthConnection | None: ...
    async def get_by_user_and_provider(
        self, user_id: uuid.UUID, provider: OAuthProvider
    ) -> OAuthConnection | None: ...
    async def save(self, connection: OAuthConnection) -> None: ...
    async def delete(self, id: uuid.UUID) -> None: ...


class OAuthStateRepository(Protocol):
    async def save(self, state: str, data: dict[str, Any]) -> None: ...
    async def get_and_delete(self, state: str) -> dict[str, Any] | None: ...
