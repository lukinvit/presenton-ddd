"""Export API request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class ExportRequest(BaseModel):
    presentation_id: str
    include_speaker_notes: bool = False
    quality: str = "high"

    @field_validator("quality")
    @classmethod
    def quality_must_be_valid(cls, v: str) -> str:
        allowed = {"high", "medium", "low"}
        if v not in allowed:
            raise ValueError(f"quality must be one of {allowed}")
        return v


class ExportJobResponse(BaseModel):
    id: str
    presentation_id: str
    format: str
    status: str
    output_path: str | None
    error_message: str | None
    created_at: str
    completed_at: str | None
