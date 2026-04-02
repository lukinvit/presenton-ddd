"""Rendering domain value objects and enumerations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

from shared.domain.value_object import ValueObject


class RenderStatus(Enum):
    PENDING = "pending"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class RenderConfig(ValueObject):
    """Configuration for a render job."""

    width: int = 1920
    height: int = 1080
    format: str = "html"
    include_css: bool = True

    def __hash__(self) -> int:
        return hash((self.width, self.height, self.format, self.include_css))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RenderConfig):
            return NotImplemented
        return (
            self.width == other.width
            and self.height == other.height
            and self.format == other.format
            and self.include_css == other.include_css
        )


@dataclass(frozen=True)
class VisualDiffResult(ValueObject):
    """Result of comparing two rendered slides visually."""

    slide_id: uuid.UUID
    difference_percent: float  # 0.0 - 100.0
    changed_regions: list[str] = field(default_factory=list)  # type: ignore[misc]

    def __hash__(self) -> int:
        return hash((self.slide_id, self.difference_percent, tuple(self.changed_regions)))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, VisualDiffResult):
            return NotImplemented
        return (
            self.slide_id == other.slide_id
            and self.difference_percent == other.difference_percent
            and self.changed_regions == other.changed_regions
        )
