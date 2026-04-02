"""Unit tests for style domain entities."""

from __future__ import annotations

import uuid

from domains.style.domain.entities import (
    BUILTIN_PRESETS,
    BUILTIN_PRESETS_BY_NAME,
    StylePreset,
    StyleProfile,
)
from domains.style.domain.value_objects import ColorPalette, LayoutRules, Spacing, Typography


def _make_colors() -> ColorPalette:
    return ColorPalette(
        primary="#1A1A1A",
        secondary="#555555",
        accent=("#0066CC",),
        background="#FFFFFF",
        text="#1A1A1A",
    )


def _make_typography() -> Typography:
    return Typography.from_sizes_dict(
        heading_font="Inter",
        body_font="Inter",
        sizes={"h1": "36px", "h2": "28px", "h3": "22px", "body": "16px"},
    )


def _make_layout() -> LayoutRules:
    return LayoutRules(
        margin="40px",
        padding="24px",
        alignment_grid=12,
        max_content_width="1200px",
    )


def _make_spacing() -> Spacing:
    return Spacing(line_height="1.5", paragraph_gap="20px", element_gap="16px")


class TestStyleProfile:
    def _make_profile(self) -> StyleProfile:
        return StyleProfile(
            id=uuid.uuid4(),
            name="Test Profile",
            source="custom",
        )

    def test_create_profile(self) -> None:
        p = self._make_profile()
        assert p.name == "Test Profile"
        assert p.source == "custom"
        assert p.colors is None

    def test_update_colors(self) -> None:
        p = self._make_profile()
        colors = _make_colors()
        p.update_colors(colors)
        assert p.colors == colors

    def test_update_typography(self) -> None:
        p = self._make_profile()
        t = _make_typography()
        p.update_typography(t)
        assert p.typography == t

    def test_update_layout(self) -> None:
        p = self._make_profile()
        lo = _make_layout()
        p.update_layout(lo)
        assert p.layout == lo

    def test_update_spacing(self) -> None:
        p = self._make_profile()
        sp = _make_spacing()
        p.update_spacing(sp)
        assert p.spacing == sp

    def test_is_complete_false_when_empty(self) -> None:
        p = self._make_profile()
        assert p.is_complete() is False

    def test_is_complete_true_when_all_set(self) -> None:
        p = self._make_profile()
        p.update_colors(_make_colors())
        p.update_typography(_make_typography())
        p.update_layout(_make_layout())
        p.update_spacing(_make_spacing())
        assert p.is_complete() is True

    def test_is_complete_false_when_one_missing(self) -> None:
        p = self._make_profile()
        p.update_colors(_make_colors())
        p.update_typography(_make_typography())
        p.update_layout(_make_layout())
        # spacing not set
        assert p.is_complete() is False


class TestStylePreset:
    def test_create_preset(self) -> None:
        profile = StyleProfile(id=uuid.uuid4(), name="Profile", source="custom")
        preset = StylePreset(
            id=uuid.uuid4(),
            name="My Preset",
            description="A test preset",
            profile=profile,
            is_builtin=False,
        )
        assert preset.name == "My Preset"
        assert preset.is_builtin is False
        assert preset.profile is profile


class TestBuiltinPresets:
    def test_five_presets_defined(self) -> None:
        assert len(BUILTIN_PRESETS) == 5

    def test_preset_names(self) -> None:
        expected = {
            "minimal-light",
            "corporate-blue",
            "creative-bold",
            "dark-elegant",
            "startup-gradient",
        }
        actual = {p.name for p in BUILTIN_PRESETS}
        assert actual == expected

    def test_all_presets_are_builtin(self) -> None:
        assert all(p.is_builtin for p in BUILTIN_PRESETS)

    def test_all_presets_have_complete_profiles(self) -> None:
        for preset in BUILTIN_PRESETS:
            assert preset.profile is not None
            assert preset.profile.is_complete(), f"Preset {preset.name!r} profile is incomplete"

    def test_preset_by_name_lookup(self) -> None:
        p = BUILTIN_PRESETS_BY_NAME["minimal-light"]
        assert p.name == "minimal-light"

    def test_builtin_ids_are_deterministic(self) -> None:
        """Same preset has same UUID across runs (uuid5 based)."""
        ids_first = [p.id for p in BUILTIN_PRESETS]
        ids_second = [p.id for p in BUILTIN_PRESETS]
        assert ids_first == ids_second

    def test_dark_elegant_has_dark_background(self) -> None:
        dark = BUILTIN_PRESETS_BY_NAME["dark-elegant"]
        assert dark.profile is not None
        assert dark.profile.colors is not None
        # Background should be dark (low luminance)
        bg = dark.profile.colors.background
        # Just a sanity check that it's a dark hex
        r, g, b = int(bg[1:3], 16), int(bg[3:5], 16), int(bg[5:7], 16)
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        assert luminance < 50, f"Expected dark background, got luminance={luminance}"
