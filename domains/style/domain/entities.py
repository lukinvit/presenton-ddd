"""Style domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from shared.domain.entity import AggregateRoot, Entity

from .value_objects import ColorPalette, LayoutRules, Spacing, Typography

# Source constants
SOURCE_FILE = "file"
SOURCE_URL = "url"
SOURCE_PRESET = "preset"
SOURCE_CUSTOM = "custom"


@dataclass
class StyleProfile(AggregateRoot):
    """Aggregate root for style configuration."""

    name: str = ""
    source: str = SOURCE_CUSTOM
    colors: ColorPalette | None = None
    typography: Typography | None = None
    layout: LayoutRules | None = None
    spacing: Spacing | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_colors(self, colors: ColorPalette) -> None:
        self.colors = colors

    def update_typography(self, typography: Typography) -> None:
        self.typography = typography

    def update_layout(self, layout: LayoutRules) -> None:
        self.layout = layout

    def update_spacing(self, spacing: Spacing) -> None:
        self.spacing = spacing

    def is_complete(self) -> bool:
        """Return True when all style sections are filled."""
        return all(x is not None for x in (self.colors, self.typography, self.layout, self.spacing))


@dataclass
class StylePreset(Entity):
    """A named, reusable style preset backed by a StyleProfile."""

    name: str = ""
    description: str = ""
    profile: StyleProfile | None = None
    is_builtin: bool = False


# ---------------------------------------------------------------------------
# Built-in presets
# ---------------------------------------------------------------------------


def _make_preset(
    name: str,
    description: str,
    colors: ColorPalette,
    typography: Typography,
    layout: LayoutRules,
    spacing: Spacing,
    *,
    is_builtin: bool = True,
) -> StylePreset:
    profile = StyleProfile(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, f"preset-profile-{name}"),
        name=name,
        source=SOURCE_PRESET,
        colors=colors,
        typography=typography,
        layout=layout,
        spacing=spacing,
    )
    return StylePreset(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, f"preset-{name}"),
        name=name,
        description=description,
        profile=profile,
        is_builtin=is_builtin,
    )


BUILTIN_PRESETS: list[StylePreset] = [
    _make_preset(
        name="minimal-light",
        description="Clean, minimal light theme with neutral tones and generous whitespace",
        colors=ColorPalette(
            primary="#1A1A1A",
            secondary="#555555",
            accent=("#0066CC",),
            background="#FFFFFF",
            text="#1A1A1A",
        ),
        typography=Typography.from_sizes_dict(
            heading_font="Inter",
            body_font="Inter",
            sizes={"h1": "40px", "h2": "32px", "h3": "24px", "body": "16px"},
        ),
        layout=LayoutRules(
            margin="48px",
            padding="32px",
            alignment_grid=12,
            max_content_width="1200px",
        ),
        spacing=Spacing(line_height="1.6", paragraph_gap="24px", element_gap="16px"),
    ),
    _make_preset(
        name="corporate-blue",
        description="Professional corporate theme with deep blues and structured layouts",
        colors=ColorPalette(
            primary="#003366",
            secondary="#0055A4",
            accent=("#FF6B00", "#00A3E0"),
            background="#F5F7FA",
            text="#1C2B3A",
        ),
        typography=Typography.from_sizes_dict(
            heading_font="Roboto",
            body_font="Roboto",
            sizes={"h1": "36px", "h2": "28px", "h3": "22px", "body": "15px"},
        ),
        layout=LayoutRules(
            margin="40px",
            padding="28px",
            alignment_grid=12,
            max_content_width="1140px",
        ),
        spacing=Spacing(line_height="1.5", paragraph_gap="20px", element_gap="14px"),
    ),
    _make_preset(
        name="creative-bold",
        description="Vibrant, expressive theme with bold colors and creative typography",
        colors=ColorPalette(
            primary="#FF3366",
            secondary="#6600CC",
            accent=("#00CCAA", "#FFCC00", "#FF6600"),
            background="#FFFFFF",
            text="#111111",
        ),
        typography=Typography.from_sizes_dict(
            heading_font="Poppins",
            body_font="DM Sans",
            sizes={"h1": "48px", "h2": "36px", "h3": "26px", "body": "17px"},
        ),
        layout=LayoutRules(
            margin="36px",
            padding="24px",
            alignment_grid=12,
            max_content_width="1280px",
        ),
        spacing=Spacing(line_height="1.7", paragraph_gap="28px", element_gap="20px"),
    ),
    _make_preset(
        name="dark-elegant",
        description="Sophisticated dark theme with elegant typography and subtle accents",
        colors=ColorPalette(
            primary="#E8E8E8",
            secondary="#AAAAAA",
            accent=("#C9A84C", "#7B68EE"),
            background="#121212",
            text="#E8E8E8",
        ),
        typography=Typography.from_sizes_dict(
            heading_font="Playfair Display",
            body_font="Lato",
            sizes={"h1": "42px", "h2": "32px", "h3": "24px", "body": "16px"},
        ),
        layout=LayoutRules(
            margin="44px",
            padding="32px",
            alignment_grid=12,
            max_content_width="1200px",
        ),
        spacing=Spacing(line_height="1.65", paragraph_gap="22px", element_gap="16px"),
    ),
    _make_preset(
        name="startup-gradient",
        description="Modern startup theme with gradient accents and energetic palette",
        colors=ColorPalette(
            primary="#6C63FF",
            secondary="#FF6584",
            accent=("#43E97B", "#FA8231", "#2C3E50"),
            background="#FAFBFF",
            text="#2C3E50",
        ),
        typography=Typography.from_sizes_dict(
            heading_font="Nunito",
            body_font="Open Sans",
            sizes={"h1": "44px", "h2": "34px", "h3": "26px", "body": "16px"},
        ),
        layout=LayoutRules(
            margin="40px",
            padding="28px",
            alignment_grid=12,
            max_content_width="1200px",
        ),
        spacing=Spacing(line_height="1.6", paragraph_gap="24px", element_gap="18px"),
    ),
]

# Lookup by name for quick access
BUILTIN_PRESETS_BY_NAME: dict[str, StylePreset] = {p.name: p for p in BUILTIN_PRESETS}
