"""Media domain repository protocols."""

from __future__ import annotations

import uuid
from typing import Protocol

from .entities import InfographicTemplate, MediaAsset


class MediaAssetRepository(Protocol):
    async def save(self, asset: MediaAsset) -> None: ...

    async def get(self, asset_id: uuid.UUID) -> MediaAsset | None: ...

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[MediaAsset]: ...

    async def delete(self, asset_id: uuid.UUID) -> None: ...


class InfographicTemplateRepository(Protocol):
    async def save(self, template: InfographicTemplate) -> None: ...

    async def get(self, template_id: uuid.UUID) -> InfographicTemplate | None: ...

    async def list_all(self) -> list[InfographicTemplate]: ...
