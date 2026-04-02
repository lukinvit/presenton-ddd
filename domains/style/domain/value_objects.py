"""Style domain value objects."""

from __future__ import annotations

import re
from dataclasses import dataclass

from shared.domain.value_object import ValueObject

_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")


def _validate_hex(color: str, field_name: str) -> str:
    if not _HEX_RE.match(color):
        raise ValueError(f"{field_name} must be a valid hex color, got: {color!r}")
    return color.upper()


@dataclass(frozen=True)
class ColorPalette(ValueObject):
    """Color palette for a style profile."""

    primary: str
    secondary: str
    accent: tuple[str, ...]  # up to 5 accent colors
    background: str
    text: str

    def __post_init__(self) -> None:
        # Validate hex colors via object.__setattr__ because frozen=True
        object.__setattr__(self, "primary", _validate_hex(self.primary, "primary"))
        object.__setattr__(self, "secondary", _validate_hex(self.secondary, "secondary"))
        object.__setattr__(self, "background", _validate_hex(self.background, "background"))
        object.__setattr__(self, "text", _validate_hex(self.text, "text"))
        validated_accent = tuple(
            _validate_hex(c, f"accent[{i}]") for i, c in enumerate(self.accent)
        )
        if len(validated_accent) > 5:
            raise ValueError("accent may contain at most 5 colors")
        object.__setattr__(self, "accent", validated_accent)

    def __hash__(self) -> int:
        return hash((self.primary, self.secondary, self.accent, self.background, self.text))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ColorPalette):
            return NotImplemented
        return (
            self.primary == other.primary
            and self.secondary == other.secondary
            and self.accent == other.accent
            and self.background == other.background
            and self.text == other.text
        )


@dataclass(frozen=True)
class Typography(ValueObject):
    """Typography settings for a style profile."""

    heading_font: str
    body_font: str
    # {"h1": "36px", "h2": "28px", "h3": "22px", "body": "16px"}
    sizes: tuple[tuple[str, str], ...]

    @classmethod
    def from_sizes_dict(
        cls,
        heading_font: str,
        body_font: str,
        sizes: dict[str, str],
    ) -> Typography:
        return cls(
            heading_font=heading_font,
            body_font=body_font,
            sizes=tuple(sorted(sizes.items())),
        )

    @property
    def sizes_dict(self) -> dict[str, str]:
        return dict(self.sizes)

    def __hash__(self) -> int:
        return hash((self.heading_font, self.body_font, self.sizes))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Typography):
            return NotImplemented
        return (
            self.heading_font == other.heading_font
            and self.body_font == other.body_font
            and self.sizes == other.sizes
        )


@dataclass(frozen=True)
class LayoutRules(ValueObject):
    """Layout rules for a style profile."""

    margin: str
    padding: str
    alignment_grid: int  # columns, e.g. 12
    max_content_width: str

    def __post_init__(self) -> None:
        if self.alignment_grid < 1:
            raise ValueError("alignment_grid must be a positive integer")

    def __hash__(self) -> int:
        return hash((self.margin, self.padding, self.alignment_grid, self.max_content_width))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LayoutRules):
            return NotImplemented
        return (
            self.margin == other.margin
            and self.padding == other.padding
            and self.alignment_grid == other.alignment_grid
            and self.max_content_width == other.max_content_width
        )


@dataclass(frozen=True)
class Spacing(ValueObject):
    """Spacing settings for a style profile."""

    line_height: str
    paragraph_gap: str
    element_gap: str

    def __hash__(self) -> int:
        return hash((self.line_height, self.paragraph_gap, self.element_gap))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Spacing):
            return NotImplemented
        return (
            self.line_height == other.line_height
            and self.paragraph_gap == other.paragraph_gap
            and self.element_gap == other.element_gap
        )
