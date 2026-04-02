"""Data Transfer Objects for the rendering domain."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RenderedSlideDTO:
    id: str
    slide_id: str
    html: str
    thumbnail_url: str | None
    render_time_ms: int


@dataclass
class RenderJobDTO:
    id: str
    presentation_id: str
    status: str
    config_width: int
    config_height: int
    config_format: str
    config_include_css: bool
    created_at: str
    completed_at: str | None
    rendered_slides: list[RenderedSlideDTO] = field(default_factory=list)


@dataclass
class VisualDiffResultDTO:
    slide_id: str
    difference_percent: float
    changed_regions: list[str] = field(default_factory=list)
