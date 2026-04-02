"""Presentation domain repository protocol."""

from __future__ import annotations

import uuid
from typing import Protocol

from .entities import Presentation


class PresentationRepository(Protocol):
    async def get(self, id: uuid.UUID) -> Presentation | None: ...
    async def save(self, presentation: Presentation) -> None: ...
    async def delete(self, id: uuid.UUID) -> None: ...
    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Presentation]: ...
