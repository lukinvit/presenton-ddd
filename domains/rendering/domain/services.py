"""Rendering domain services and external service protocols."""

from __future__ import annotations

import random
import uuid
from typing import Any, Protocol

from .value_objects import VisualDiffResult


class HTMLRenderer(Protocol):
    """Render slide data + CSS variables into HTML."""

    async def render(self, slide_data: dict[str, Any], css_variables: str) -> str: ...


class ScreenshotRenderer(Protocol):
    """Capture HTML as a PNG screenshot (e.g. via Puppeteer/Chromium)."""

    async def capture(self, html: str, width: int, height: int) -> bytes: ...


class VisualDiffService:
    """Compare two rendered slides and return a diff result.

    Current implementation is a pixel-comparison stub that returns a random
    difference percentage; replace with a real image-comparison library when
    a screenshot renderer is available.
    """

    def compute_diff(self, slide_id: uuid.UUID, image_a: bytes, image_b: bytes) -> VisualDiffResult:
        if image_a == image_b:
            return VisualDiffResult(slide_id=slide_id, difference_percent=0.0, changed_regions=[])

        # Stub: derive a deterministic-ish random diff from the image sizes
        rng = random.Random(len(image_a) ^ len(image_b))
        diff_pct = round(rng.uniform(0.1, 100.0), 2)
        changed_regions = ["main-content"] if diff_pct > 5.0 else ["minor-change"]
        return VisualDiffResult(
            slide_id=slide_id,
            difference_percent=diff_pct,
            changed_regions=changed_regions,
        )
