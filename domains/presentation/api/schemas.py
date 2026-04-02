"""Pydantic request/response schemas for the presentation API."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreatePresentationRequest(BaseModel):
    title: str
    description: str = ""

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Title must not be empty")
        return v.strip()


class UpdatePresentationRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class SlideElementRequest(BaseModel):
    type: str
    content: str
    position: dict[str, Any] = {}
    style: dict[str, Any] = {}


class AddSlideRequest(BaseModel):
    title: str
    layout_type: str = "content"
    index: int | None = None
    speaker_notes: str = ""

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Title must not be empty")
        return v.strip()


class UpdateSlideRequest(BaseModel):
    title: str | None = None
    elements: list[SlideElementRequest] | None = None
    speaker_notes: str | None = None


class ReorderSlidesRequest(BaseModel):
    slide_ids: list[UUID]


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SlideElementResponse(BaseModel):
    type: str
    content: str
    position: dict[str, Any]
    style: dict[str, Any]


class SlideResponse(BaseModel):
    id: str
    presentation_id: str
    index: int
    title: str
    layout_type: str
    speaker_notes: str
    elements: list[SlideElementResponse]


class PresentationResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str
    template_id: str | None
    style_profile_id: str | None
    created_at: str
    updated_at: str
    slides: list[SlideResponse]
