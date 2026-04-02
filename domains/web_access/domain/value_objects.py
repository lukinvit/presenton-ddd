from __future__ import annotations

from enum import Enum


class SearchEngine(Enum):
    DUCKDUCKGO = "duckduckgo"
    GOOGLE = "google"


class ContentFormat(Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
