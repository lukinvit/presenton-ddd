from __future__ import annotations

from typing import Protocol

from .entities import WebResult
from .value_objects import ContentFormat


class WebSearchAdapter(Protocol):
    """External search engine adapter."""

    async def search(self, query: str, max_results: int = 10) -> list[WebResult]: ...


class WebFetchAdapter(Protocol):
    """Fetch and convert web pages to various formats."""

    async def fetch(self, url: str, format: ContentFormat = ContentFormat.MARKDOWN) -> str: ...


class ScreenshotAdapter(Protocol):
    """Take screenshots of URLs."""

    async def screenshot(
        self,
        url: str,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ) -> bytes: ...
