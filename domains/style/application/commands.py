"""Style application commands."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from domains.style.application.dto import (
    ColorPaletteDTO,
    LayoutRulesDTO,
    PresetDTO,
    SpacingDTO,
    StyleProfileDTO,
    TypographyDTO,
    ValidationResultDTO,
)
from domains.style.domain.entities import StylePreset, StyleProfile
from domains.style.domain.events import (
    EVENT_STYLE_APPLIED,
    EVENT_STYLE_PRESET_CREATED,
    EVENT_STYLE_PROFILE_CREATED,
)
from domains.style.domain.repositories import StylePresetRepository, StyleProfileRepository
from domains.style.domain.services import (
    StyleExtractionService,
    StyleToCSS,
    StyleValidationService,
)
from domains.style.domain.value_objects import ColorPalette, LayoutRules, Spacing, Typography
from shared.domain.events import DomainEvent, EventBus

# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _profile_to_dto(p: StyleProfile) -> StyleProfileDTO:
    colors_dto = None
    if p.colors:
        colors_dto = ColorPaletteDTO(
            primary=p.colors.primary,
            secondary=p.colors.secondary,
            accent=list(p.colors.accent),
            background=p.colors.background,
            text=p.colors.text,
        )
    typo_dto = None
    if p.typography:
        typo_dto = TypographyDTO(
            heading_font=p.typography.heading_font,
            body_font=p.typography.body_font,
            sizes=p.typography.sizes_dict,
        )
    layout_dto = None
    if p.layout:
        layout_dto = LayoutRulesDTO(
            margin=p.layout.margin,
            padding=p.layout.padding,
            alignment_grid=p.layout.alignment_grid,
            max_content_width=p.layout.max_content_width,
        )
    spacing_dto = None
    if p.spacing:
        spacing_dto = SpacingDTO(
            line_height=p.spacing.line_height,
            paragraph_gap=p.spacing.paragraph_gap,
            element_gap=p.spacing.element_gap,
        )
    return StyleProfileDTO(
        id=str(p.id),
        name=p.name,
        source=p.source,
        created_at=p.created_at.isoformat(),
        colors=colors_dto,
        typography=typo_dto,
        layout=layout_dto,
        spacing=spacing_dto,
    )


def _preset_to_dto(preset: StylePreset) -> PresetDTO:
    return PresetDTO(
        id=str(preset.id),
        name=preset.name,
        description=preset.description,
        is_builtin=preset.is_builtin,
        profile=_profile_to_dto(preset.profile) if preset.profile else None,
    )


def _raw_style_to_profile(raw: dict, name: str, profile_id: uuid.UUID) -> StyleProfile:
    """Build a StyleProfile entity from the raw dict returned by extraction services."""
    colors_raw = raw.get("colors", {})
    colors = ColorPalette(
        primary=colors_raw.get("primary", "#000000"),
        secondary=colors_raw.get("secondary", "#000000"),
        accent=tuple(colors_raw.get("accent", [])),
        background=colors_raw.get("background", "#FFFFFF"),
        text=colors_raw.get("text", "#000000"),
    )

    typo_raw = raw.get("typography", {})
    typography = Typography.from_sizes_dict(
        heading_font=typo_raw.get("heading_font", "Arial"),
        body_font=typo_raw.get("body_font", "Arial"),
        sizes=typo_raw.get("sizes", {"h1": "36px", "h2": "28px", "h3": "22px", "body": "16px"}),
    )

    layout_raw = raw.get("layout", {})
    layout = LayoutRules(
        margin=layout_raw.get("margin", "40px"),
        padding=layout_raw.get("padding", "24px"),
        alignment_grid=layout_raw.get("alignment_grid", 12),
        max_content_width=layout_raw.get("max_content_width", "1200px"),
    )

    spacing_raw = raw.get("spacing", {})
    spacing = Spacing(
        line_height=spacing_raw.get("line_height", "1.5"),
        paragraph_gap=spacing_raw.get("paragraph_gap", "20px"),
        element_gap=spacing_raw.get("element_gap", "16px"),
    )

    return StyleProfile(
        id=profile_id,
        name=name,
        source=raw.get("source", "custom"),
        colors=colors,
        typography=typography,
        layout=layout,
        spacing=spacing,
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@dataclass
class ExtractStyleFromFileCommand:
    """Extract a StyleProfile from a PPTX or PDF file."""

    repo: StyleProfileRepository
    event_bus: EventBus
    extraction_service: StyleExtractionService | None = None

    def __post_init__(self) -> None:
        if self.extraction_service is None:
            self.extraction_service = StyleExtractionService()

    async def execute(self, file_path: str, name: str) -> StyleProfileDTO:
        raw = self.extraction_service.extract_from_file(file_path, name)  # type: ignore[union-attr]
        profile = _raw_style_to_profile(raw, name, uuid.uuid4())
        await self.repo.save(profile)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=profile.id,
                event_type=EVENT_STYLE_PROFILE_CREATED,
                payload={"profile_id": str(profile.id), "name": name, "source": "file"},
            )
        )
        return _profile_to_dto(profile)


@dataclass
class ExtractStyleFromURLCommand:
    """Extract a StyleProfile from a URL via vision."""

    repo: StyleProfileRepository
    event_bus: EventBus
    extraction_service: StyleExtractionService | None = None

    def __post_init__(self) -> None:
        if self.extraction_service is None:
            self.extraction_service = StyleExtractionService()

    async def execute(self, url: str, name: str) -> StyleProfileDTO:
        raw = self.extraction_service.extract_from_url(url, name)  # type: ignore[union-attr]
        profile = _raw_style_to_profile(raw, name, uuid.uuid4())
        await self.repo.save(profile)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=profile.id,
                event_type=EVENT_STYLE_PROFILE_CREATED,
                payload={"profile_id": str(profile.id), "name": name, "source": "url"},
            )
        )
        return _profile_to_dto(profile)


@dataclass
class CreatePresetCommand:
    """Create a new style preset from an existing profile."""

    profile_repo: StyleProfileRepository
    preset_repo: StylePresetRepository
    event_bus: EventBus

    async def execute(
        self,
        name: str,
        description: str,
        profile_id: uuid.UUID,
    ) -> PresetDTO:
        profile = await self.profile_repo.get(profile_id)
        if profile is None:
            raise ValueError(f"StyleProfile '{profile_id}' not found")

        preset = StylePreset(
            id=uuid.uuid4(),
            name=name,
            description=description,
            profile=profile,
            is_builtin=False,
        )
        await self.preset_repo.save(preset)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=preset.id,
                event_type=EVENT_STYLE_PRESET_CREATED,
                payload={"preset_id": str(preset.id), "name": name},
            )
        )
        return _preset_to_dto(preset)


@dataclass
class ApplyStyleCommand:
    """Apply a StyleProfile to a presentation (publishes StyleApplied event)."""

    profile_repo: StyleProfileRepository
    event_bus: EventBus

    async def execute(self, presentation_id: uuid.UUID, profile_id: uuid.UUID) -> None:
        profile = await self.profile_repo.get(profile_id)
        if profile is None:
            raise ValueError(f"StyleProfile '{profile_id}' not found")

        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=presentation_id,
                event_type=EVENT_STYLE_APPLIED,
                payload={
                    "presentation_id": str(presentation_id),
                    "profile_id": str(profile_id),
                },
            )
        )


@dataclass
class ValidateStyleCommand:
    """Validate rendered presentation data against a style profile."""

    profile_repo: StyleProfileRepository
    validation_service: StyleValidationService | None = None

    def __post_init__(self) -> None:
        if self.validation_service is None:
            self.validation_service = StyleValidationService()

    async def execute(self, profile_id: uuid.UUID, rendered_data: dict) -> ValidationResultDTO:
        profile = await self.profile_repo.get(profile_id)
        if profile is None:
            raise ValueError(f"StyleProfile '{profile_id}' not found")

        criteria = self.validation_service.validate(profile, rendered_data)  # type: ignore[union-attr]
        return ValidationResultDTO(profile_id=str(profile_id), criteria=criteria)


@dataclass
class GetCSSCommand:
    """Convert a StyleProfile to CSS custom properties."""

    profile_repo: StyleProfileRepository
    css_service: StyleToCSS | None = None

    def __post_init__(self) -> None:
        if self.css_service is None:
            self.css_service = StyleToCSS()

    async def execute(self, profile_id: uuid.UUID) -> str:
        profile = await self.profile_repo.get(profile_id)
        if profile is None:
            raise ValueError(f"StyleProfile '{profile_id}' not found")
        return self.css_service.to_css_variables(profile)  # type: ignore[union-attr]


@dataclass
class GetTailwindCommand:
    """Convert a StyleProfile to a Tailwind theme dict."""

    profile_repo: StyleProfileRepository
    css_service: StyleToCSS | None = None

    def __post_init__(self) -> None:
        if self.css_service is None:
            self.css_service = StyleToCSS()

    async def execute(self, profile_id: uuid.UUID) -> dict:
        profile = await self.profile_repo.get(profile_id)
        if profile is None:
            raise ValueError(f"StyleProfile '{profile_id}' not found")
        return self.css_service.to_tailwind_theme(profile)  # type: ignore[union-attr]
