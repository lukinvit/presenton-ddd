"""Pydantic request/response schemas for the style API."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Sub-schemas
# ---------------------------------------------------------------------------


class ColorPaletteSchema(BaseModel):
    primary: str
    secondary: str
    accent: list[str] = []
    background: str
    text: str


class TypographySchema(BaseModel):
    heading_font: str
    body_font: str
    sizes: dict[str, str] = {}


class LayoutRulesSchema(BaseModel):
    margin: str
    padding: str
    alignment_grid: int
    max_content_width: str


class SpacingSchema(BaseModel):
    line_height: str
    paragraph_gap: str
    element_gap: str


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ExtractFromFileRequest(BaseModel):
    file_path: str
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()


class ExtractFromURLRequest(BaseModel):
    url: str
    name: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()


class CreatePresetRequest(BaseModel):
    name: str
    description: str = ""
    profile_id: UUID

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()


class ValidateStyleRequest(BaseModel):
    colors: list[str] = []
    fonts: list[str] = []
    bg_color: str = ""


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ColorPaletteResponse(BaseModel):
    primary: str
    secondary: str
    accent: list[str]
    background: str
    text: str


class TypographyResponse(BaseModel):
    heading_font: str
    body_font: str
    sizes: dict[str, str]


class LayoutRulesResponse(BaseModel):
    margin: str
    padding: str
    alignment_grid: int
    max_content_width: str


class SpacingResponse(BaseModel):
    line_height: str
    paragraph_gap: str
    element_gap: str


class StyleProfileResponse(BaseModel):
    id: str
    name: str
    source: str
    created_at: str
    colors: ColorPaletteResponse | None = None
    typography: TypographyResponse | None = None
    layout: LayoutRulesResponse | None = None
    spacing: SpacingResponse | None = None


class PresetResponse(BaseModel):
    id: str
    name: str
    description: str
    is_builtin: bool
    profile: StyleProfileResponse | None = None


class ValidationCriterionResponse(BaseModel):
    criterion: str
    passed: bool
    details: str


class ValidationResultResponse(BaseModel):
    profile_id: str
    passed: bool
    criteria: list[ValidationCriterionResponse]


class CSSResponse(BaseModel):
    profile_id: str
    css: str


class TailwindResponse(BaseModel):
    profile_id: str
    theme: dict[str, Any]
