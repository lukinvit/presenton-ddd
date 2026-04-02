from __future__ import annotations

import uuid
from typing import Protocol, TypeVar, runtime_checkable

from shared.domain.entity import Entity

T = TypeVar("T", bound=Entity)


@runtime_checkable
class Repository(Protocol[T]):
    async def get(self, id: uuid.UUID) -> T | None: ...
    async def save(self, entity: T) -> None: ...
    async def delete(self, id: uuid.UUID) -> None: ...
