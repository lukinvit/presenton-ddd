"""Data Transfer Objects for the content domain."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OutlineItemDTO:
    index: int
    title: str
    key_points: list[str]
    suggested_layout: str


@dataclass
class ContentPlanDTO:
    id: str
    presentation_id: str
    topic: str
    created_at: str
    outline: list[OutlineItemDTO] = field(default_factory=list)


@dataclass
class SlideContentDTO:
    id: str
    plan_id: str
    slide_index: int
    title: str
    body: str
    speaker_notes: str
    generated_at: str


@dataclass
class SystemPromptDTO:
    id: str
    name: str
    prompt_text: str
    variables: list[str]
    is_default: bool
    updated_at: str
