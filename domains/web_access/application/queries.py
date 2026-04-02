from __future__ import annotations

import uuid
from dataclasses import dataclass

from domains.web_access.application.dto import WebQueryDTO, WebResultDTO
from domains.web_access.domain.repositories import WebQueryRepository


@dataclass
class GetCachedResultQuery:
    """Retrieve a previously cached web search result by its ID."""

    query_repo: WebQueryRepository

    async def execute(self, query_id: uuid.UUID) -> WebQueryDTO | None:
        web_query = await self.query_repo.get(query_id)
        if web_query is None:
            return None
        return WebQueryDTO(
            id=web_query.id,
            query=web_query.query,
            engine=web_query.engine.value,
            results=[
                WebResultDTO(title=r.title, url=r.url, snippet=r.snippet) for r in web_query.results
            ],
            created_at=web_query.created_at,
            cached_until=web_query.cached_until,
        )
