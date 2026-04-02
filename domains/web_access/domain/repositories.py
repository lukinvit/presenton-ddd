from __future__ import annotations

import uuid
from typing import Protocol

from .entities import WebQuery
from .value_objects import SearchEngine


class WebQueryRepository(Protocol):
    """Repository for caching web search results."""

    async def get(self, id: uuid.UUID) -> WebQuery | None: ...
    async def find_cached(self, query: str, engine: SearchEngine) -> WebQuery | None: ...
    async def save(self, web_query: WebQuery) -> None: ...
    async def delete(self, id: uuid.UUID) -> None: ...
