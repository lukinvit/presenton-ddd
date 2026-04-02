"""Data Transfer Objects for the presentation domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SlideElementDTO:
    type: str
    content: str
    position: dict[str, Any]
    style: dict[str, Any]


@dataclass
class SlideDTO:
    id: str
    presentation_id: str
    index: int
    title: str
    layout_type: str
    speaker_notes: str
    elements: list[SlideElementDTO] = field(default_factory=list)


@dataclass
class PresentationDTO:
    id: str
    title: str
    description: str
    status: str
    template_id: str | None
    style_profile_id: str | None
    created_at: str
    updated_at: str
    slides: list[SlideDTO] = field(default_factory=list)
