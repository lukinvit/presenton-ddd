"""Data Transfer Objects for the media domain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MediaAssetDTO:
    id: str
    type: str
    url: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class InfographicTemplateDTO:
    id: str
    name: str
    required_data_fields: list[str] = field(default_factory=list)
    is_builtin: bool = False
