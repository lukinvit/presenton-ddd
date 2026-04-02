from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from shared.domain.entity import AggregateRoot, Entity
from shared.domain.value_object import ValueObject

from .value_objects import ContentFormat, SearchEngine


@dataclass(frozen=True)
class WebResult(ValueObject):
    """A single search result — title, URL and snippet."""

    title: str
    url: str
    snippet: str


@dataclass(eq=False)
class WebQuery(AggregateRoot):
    """Aggregate root representing a web search query and its cached results."""

    query: str = ""
    engine: SearchEngine = SearchEngine.DUCKDUCKGO
    results: list[WebResult] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    cached_until: datetime | None = None

    def set_results(self, results: list[WebResult]) -> None:
        self.results = list(results)

    def is_cache_valid(self) -> bool:
        if self.cached_until is None:
            return False
        return datetime.now(UTC) < self.cached_until


@dataclass(eq=False)
class ScrapedPage(Entity):
    """Entity representing a fetched and converted web page."""

    url: str = ""
    content: str = ""
    format: ContentFormat = ContentFormat.MARKDOWN
    fetched_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @classmethod
    def create(
        cls,
        url: str,
        content: str,
        format: ContentFormat = ContentFormat.MARKDOWN,
    ) -> ScrapedPage:
        return cls(
            id=uuid.uuid4(),
            url=url,
            content=content,
            format=format,
        )
