"""Data Transfer Objects for the style domain."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ColorPaletteDTO:
    primary: str
    secondary: str
    accent: list[str]
    background: str
    text: str


@dataclass
class TypographyDTO:
    heading_font: str
    body_font: str
    sizes: dict[str, str]


@dataclass
class LayoutRulesDTO:
    margin: str
    padding: str
    alignment_grid: int
    max_content_width: str


@dataclass
class SpacingDTO:
    line_height: str
    paragraph_gap: str
    element_gap: str


@dataclass
class StyleProfileDTO:
    id: str
    name: str
    source: str
    created_at: str
    colors: ColorPaletteDTO | None = None
    typography: TypographyDTO | None = None
    layout: LayoutRulesDTO | None = None
    spacing: SpacingDTO | None = None


@dataclass
class PresetDTO:
    id: str
    name: str
    description: str
    is_builtin: bool
    profile: StyleProfileDTO | None = None


@dataclass
class ValidationResultDTO:
    profile_id: str
    criteria: list[dict] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.get("passed", False) for c in self.criteria)
