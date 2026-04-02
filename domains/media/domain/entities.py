"""Media domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from shared.domain.entity import AggregateRoot, Entity

from .value_objects import AssetType


@dataclass
class MediaAsset(AggregateRoot):
    """Aggregate root representing a media asset (image, infographic, icon)."""

    type: AssetType = AssetType.IMAGE
    url: str = ""
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class InfographicTemplate(Entity):
    """A reusable SVG infographic template with placeholder variables."""

    name: str = ""
    svg_template: str = ""
    required_data_fields: list[str] = field(default_factory=list)
    is_builtin: bool = False
