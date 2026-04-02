from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SearchEngineValue = Literal["duckduckgo", "google"]
ContentFormatValue = Literal["markdown", "html", "text"]


class SearchRequest(BaseModel):
    query: str
    engine: SearchEngineValue = "duckduckgo"
    max_results: int = 10


class FetchRequest(BaseModel):
    url: str
    format: ContentFormatValue = "markdown"


class ScreenshotRequest(BaseModel):
    url: str
    viewport_width: int = 1920
    viewport_height: int = 1080


class ExtractRequest(BaseModel):
    url: str


class WebResultSchema(BaseModel):
    title: str
    url: str
    snippet: str


class WebQueryResponse(BaseModel):
    id: uuid.UUID
    query: str
    engine: str
    results: list[WebResultSchema]
    created_at: datetime
    cached_until: datetime | None = None


class ScrapedPageResponse(BaseModel):
    id: uuid.UUID
    url: str
    content: str
    format: str
    fetched_at: datetime
