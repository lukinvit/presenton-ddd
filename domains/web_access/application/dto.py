from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WebResultDTO:
    title: str
    url: str
    snippet: str


@dataclass
class WebQueryDTO:
    id: uuid.UUID
    query: str
    engine: str
    results: list[WebResultDTO] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    cached_until: datetime | None = None


@dataclass
class ScrapedPageDTO:
    id: uuid.UUID
    url: str
    content: str
    format: str
    fetched_at: datetime = field(default_factory=datetime.utcnow)
