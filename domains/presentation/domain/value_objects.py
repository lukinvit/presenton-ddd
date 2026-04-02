"""Presentation domain value objects and enumerations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from shared.domain.value_object import ValueObject


class PresentationStatus(Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    REVIEW = "review"
    FINAL = "final"


class ElementType(Enum):
    TEXT = "text"
    IMAGE = "image"
    INFOGRAPHIC = "infographic"
    ICON = "icon"
    CHART = "chart"


@dataclass(frozen=True)
class SlideElement(ValueObject):
    """An element placed on a slide (value object — no identity)."""

    type: ElementType
    content: str
    position: dict[str, Any]
    style: dict[str, Any]

    def __hash__(self) -> int:
        # dicts are not hashable; use repr for hashing
        return hash((self.type, self.content, repr(self.position), repr(self.style)))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SlideElement):
            return NotImplemented
        return (
            self.type == other.type
            and self.content == other.content
            and self.position == other.position
            and self.style == other.style
        )
