"""Pydantic request/response schemas for the content API."""

from __future__ import annotations

from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class GenerateOutlineRequest(BaseModel):
    topic: str
    num_slides: int = 5
    tone: str = "professional"
    language: str = "English"
    presentation_id: str | None = None

    @field_validator("topic")
    @classmethod
    def topic_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Topic must not be empty")
        return v.strip()

    @field_validator("num_slides")
    @classmethod
    def num_slides_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("num_slides must be at least 1")
        return v


class GenerateSlideRequest(BaseModel):
    """No body needed — plan_id and slide_index come from URL path."""


class ReviseContentRequest(BaseModel):
    feedback: str

    @field_validator("feedback")
    @classmethod
    def feedback_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Feedback must not be empty")
        return v.strip()


class CreateSystemPromptRequest(BaseModel):
    name: str
    prompt_text: str
    variables: list[str] = []
    is_default: bool = False

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Name must not be empty")
        return v.strip()


class UpdateSystemPromptRequest(BaseModel):
    prompt_text: str | None = None
    variables: list[str] | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class OutlineItemResponse(BaseModel):
    index: int
    title: str
    key_points: list[str]
    suggested_layout: str


class ContentPlanResponse(BaseModel):
    id: str
    presentation_id: str
    topic: str
    created_at: str
    outline: list[OutlineItemResponse]


class SlideContentResponse(BaseModel):
    id: str
    plan_id: str
    slide_index: int
    title: str
    body: str
    speaker_notes: str
    generated_at: str


class SystemPromptResponse(BaseModel):
    id: str
    name: str
    prompt_text: str
    variables: list[str]
    is_default: bool
    updated_at: str
