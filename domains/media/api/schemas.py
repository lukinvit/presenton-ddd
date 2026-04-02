"""Pydantic request/response schemas for the media API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SearchImagesRequest(BaseModel):
    query: str
    max_results: int = 10
    source: str | None = None


class GenerateImageRequest(BaseModel):
    prompt: str
    provider: str | None = None
    size: str = "1024x1024"


class CreateInfographicRequest(BaseModel):
    type: str
    data: dict[str, Any]
    template_id: str | None = None


class SearchIconsRequest(BaseModel):
    query: str
    max_results: int = 10


class MediaAssetResponse(BaseModel):
    id: str
    type: str
    url: str
    source: str
    metadata: dict[str, Any] = {}
    created_at: str = ""


class InfographicTemplateResponse(BaseModel):
    id: str
    name: str
    required_data_fields: list[str] = []
    is_builtin: bool = False
