"""Pydantic request/response schemas for the rendering API."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RenderConfigRequest(BaseModel):
    width: int = 1920
    height: int = 1080
    format: str = "html"
    include_css: bool = True


class RenderSlideRequest(BaseModel):
    slide_id: UUID
    slide_data: dict[str, Any] = {}
    css_variables: str = ""
    config: RenderConfigRequest = RenderConfigRequest()


class SlideDataItem(BaseModel):
    slide_id: UUID
    data: dict[str, Any] = {}


class RenderPresentationRequest(BaseModel):
    slides_data: list[SlideDataItem] = []
    css_variables: str = ""
    config: RenderConfigRequest = RenderConfigRequest()


class VisualDiffRequest(BaseModel):
    slide_id: UUID
    image_a: bytes
    image_b: bytes


class BatchRenderRequest(BaseModel):
    slides_data: list[SlideDataItem] = []
    css_variables: str = ""


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class RenderedSlideResponse(BaseModel):
    id: str
    slide_id: str
    html: str
    thumbnail_url: str | None
    render_time_ms: int


class RenderJobResponse(BaseModel):
    id: str
    presentation_id: str
    status: str
    config_width: int
    config_height: int
    config_format: str
    config_include_css: bool
    created_at: str
    completed_at: str | None
    rendered_slides: list[RenderedSlideResponse]


class VisualDiffResponse(BaseModel):
    slide_id: str
    difference_percent: float
    changed_regions: list[str]
