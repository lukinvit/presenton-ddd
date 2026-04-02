"""Rendering domain repository protocols."""

from __future__ import annotations

import uuid
from typing import Protocol

from .entities import RenderJob


class RenderJobRepository(Protocol):
    async def get(self, id: uuid.UUID) -> RenderJob | None: ...
    async def save(self, job: RenderJob) -> None: ...
    async def list_all(self, limit: int = 50, offset: int = 0) -> list[RenderJob]: ...
