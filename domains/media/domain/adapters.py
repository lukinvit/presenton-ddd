"""Media domain adapter protocols for external services."""

from __future__ import annotations

from typing import Protocol


class ImageSearchAdapter(Protocol):
    """Protocol for image search services (Pexels, Pixabay, etc.)."""

    async def search(self, query: str, max_results: int = 10) -> list[dict]: ...


class ImageGenerationAdapter(Protocol):
    """Protocol for AI image generation services (DALL-E, Gemini, etc.)."""

    async def generate(self, prompt: str, size: str = "1024x1024") -> str: ...
