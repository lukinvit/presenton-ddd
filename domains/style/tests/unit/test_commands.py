"""Unit tests for style application commands."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from domains.style.application.commands import (
    ApplyStyleCommand,
    CreatePresetCommand,
    ExtractStyleFromFileCommand,
    ExtractStyleFromURLCommand,
    GetCSSCommand,
    GetTailwindCommand,
    ValidateStyleCommand,
)
from domains.style.domain.entities import StyleProfile
from domains.style.domain.value_objects import ColorPalette, LayoutRules, Spacing, Typography

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_full_profile() -> StyleProfile:
    profile = StyleProfile(id=uuid.uuid4(), name="Test Profile", source="custom")
    profile.update_colors(
        ColorPalette(
            primary="#1A1A1A",
            secondary="#555555",
            accent=("#0066CC",),
            background="#FFFFFF",
            text="#1A1A1A",
        )
    )
    profile.update_typography(
        Typography.from_sizes_dict(
            heading_font="Inter",
            body_font="Inter",
            sizes={"h1": "36px", "h2": "28px", "h3": "22px", "body": "16px"},
        )
    )
    profile.update_layout(
        LayoutRules(
            margin="40px",
            padding="24px",
            alignment_grid=12,
            max_content_width="1200px",
        )
    )
    profile.update_spacing(Spacing(line_height="1.5", paragraph_gap="20px", element_gap="16px"))
    return profile


def _make_profile_repo(profiles: list[StyleProfile] | None = None) -> AsyncMock:
    store: dict[uuid.UUID, StyleProfile] = {p.id: p for p in (profiles or [])}
    repo = AsyncMock()

    async def get(id: uuid.UUID) -> StyleProfile | None:
        return store.get(id)

    async def save(profile: StyleProfile) -> None:
        store[profile.id] = profile

    async def delete(id: uuid.UUID) -> None:
        store.pop(id, None)

    async def list_all(limit: int = 50, offset: int = 0) -> list[StyleProfile]:
        items = list(store.values())
        return items[offset : offset + limit]

    repo.get = AsyncMock(side_effect=get)
    repo.save = AsyncMock(side_effect=save)
    repo.delete = AsyncMock(side_effect=delete)
    repo.list_all = AsyncMock(side_effect=list_all)
    return repo


def _make_preset_repo() -> AsyncMock:
    from domains.style.domain.entities import StylePreset

    store: dict[uuid.UUID, StylePreset] = {}
    repo = AsyncMock()

    async def get(id: uuid.UUID):
        return store.get(id)

    async def get_by_name(name: str):
        return next((p for p in store.values() if p.name == name), None)

    async def save(preset: StylePreset) -> None:
        store[preset.id] = preset

    async def list_all(limit: int = 100, offset: int = 0):
        items = list(store.values())
        return items[offset : offset + limit]

    repo.get = AsyncMock(side_effect=get)
    repo.get_by_name = AsyncMock(side_effect=get_by_name)
    repo.save = AsyncMock(side_effect=save)
    repo.list_all = AsyncMock(side_effect=list_all)
    return repo


def _make_event_bus() -> AsyncMock:
    bus = AsyncMock()
    bus.publish = AsyncMock()
    return bus


# ---------------------------------------------------------------------------
# ExtractStyleFromFileCommand
# ---------------------------------------------------------------------------


class TestExtractStyleFromFileCommand:
    async def test_extract_saves_profile_and_publishes_event(self, tmp_path) -> None:
        # Create a real dummy file so the service doesn't raise FileNotFoundError
        dummy = tmp_path / "deck.pptx"
        dummy.write_bytes(b"dummy")

        repo = _make_profile_repo()
        bus = _make_event_bus()
        cmd = ExtractStyleFromFileCommand(repo=repo, event_bus=bus)
        result = await cmd.execute(file_path=str(dummy), name="My Deck")

        assert result.name == "My Deck"
        assert result.source == "file"
        assert result.colors is not None
        repo.save.assert_called_once()
        bus.publish.assert_called_once()

    async def test_extract_nonexistent_file_raises(self) -> None:
        repo = _make_profile_repo()
        bus = _make_event_bus()
        cmd = ExtractStyleFromFileCommand(repo=repo, event_bus=bus)
        with pytest.raises(FileNotFoundError):
            await cmd.execute(file_path="/no/such/file.pptx", name="Bad")

    async def test_extract_unsupported_extension_raises(self, tmp_path) -> None:
        dummy = tmp_path / "deck.docx"
        dummy.write_bytes(b"dummy")
        repo = _make_profile_repo()
        bus = _make_event_bus()
        cmd = ExtractStyleFromFileCommand(repo=repo, event_bus=bus)
        with pytest.raises(ValueError, match="Unsupported"):
            await cmd.execute(file_path=str(dummy), name="Bad")


# ---------------------------------------------------------------------------
# ExtractStyleFromURLCommand
# ---------------------------------------------------------------------------


class TestExtractStyleFromURLCommand:
    async def test_extract_from_url_creates_profile(self) -> None:
        repo = _make_profile_repo()
        bus = _make_event_bus()
        cmd = ExtractStyleFromURLCommand(repo=repo, event_bus=bus)
        result = await cmd.execute(url="https://example.com", name="Example Site")

        assert result.name == "Example Site"
        assert result.source == "url"
        repo.save.assert_called_once()
        bus.publish.assert_called_once()


# ---------------------------------------------------------------------------
# CreatePresetCommand
# ---------------------------------------------------------------------------


class TestCreatePresetCommand:
    async def test_create_preset_from_existing_profile(self) -> None:
        profile = _make_full_profile()
        profile_repo = _make_profile_repo([profile])
        preset_repo = _make_preset_repo()
        bus = _make_event_bus()

        cmd = CreatePresetCommand(profile_repo=profile_repo, preset_repo=preset_repo, event_bus=bus)
        result = await cmd.execute(
            name="My Preset", description="A great preset", profile_id=profile.id
        )

        assert result.name == "My Preset"
        assert result.is_builtin is False
        assert result.profile is not None
        preset_repo.save.assert_called_once()
        bus.publish.assert_called_once()

    async def test_create_preset_missing_profile_raises(self) -> None:
        profile_repo = _make_profile_repo()
        preset_repo = _make_preset_repo()
        bus = _make_event_bus()

        cmd = CreatePresetCommand(profile_repo=profile_repo, preset_repo=preset_repo, event_bus=bus)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(name="X", description="", profile_id=uuid.uuid4())


# ---------------------------------------------------------------------------
# ApplyStyleCommand
# ---------------------------------------------------------------------------


class TestApplyStyleCommand:
    async def test_apply_publishes_event(self) -> None:
        profile = _make_full_profile()
        repo = _make_profile_repo([profile])
        bus = _make_event_bus()

        cmd = ApplyStyleCommand(profile_repo=repo, event_bus=bus)
        presentation_id = uuid.uuid4()
        await cmd.execute(presentation_id=presentation_id, profile_id=profile.id)

        bus.publish.assert_called_once()
        event = bus.publish.call_args[0][0]
        assert event.payload["presentation_id"] == str(presentation_id)
        assert event.payload["profile_id"] == str(profile.id)

    async def test_apply_missing_profile_raises(self) -> None:
        repo = _make_profile_repo()
        bus = _make_event_bus()

        cmd = ApplyStyleCommand(profile_repo=repo, event_bus=bus)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(presentation_id=uuid.uuid4(), profile_id=uuid.uuid4())


# ---------------------------------------------------------------------------
# ValidateStyleCommand
# ---------------------------------------------------------------------------


class TestValidateStyleCommand:
    async def test_validate_all_colors_in_palette(self) -> None:
        profile = _make_full_profile()
        repo = _make_profile_repo([profile])

        cmd = ValidateStyleCommand(profile_repo=repo)
        result = await cmd.execute(
            profile_id=profile.id,
            rendered_data={
                "colors": ["#1A1A1A", "#FFFFFF"],
                "fonts": ["inter"],
                "bg_color": "#FFFFFF",
            },
        )

        assert result.profile_id == str(profile.id)
        # Find color_consistency criterion
        cc = next(c for c in result.criteria if c["criterion"] == "color_consistency")
        assert cc["passed"] is True

    async def test_validate_unknown_color_fails(self) -> None:
        profile = _make_full_profile()
        repo = _make_profile_repo([profile])

        cmd = ValidateStyleCommand(profile_repo=repo)
        result = await cmd.execute(
            profile_id=profile.id,
            rendered_data={"colors": ["#DEADBE"], "fonts": [], "bg_color": ""},
        )

        cc = next(c for c in result.criteria if c["criterion"] == "color_consistency")
        assert cc["passed"] is False
        assert "#DEADBE" in cc["details"]

    async def test_validate_missing_profile_raises(self) -> None:
        repo = _make_profile_repo()
        cmd = ValidateStyleCommand(profile_repo=repo)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(profile_id=uuid.uuid4(), rendered_data={})


# ---------------------------------------------------------------------------
# GetCSSCommand
# ---------------------------------------------------------------------------


class TestGetCSSCommand:
    async def test_get_css_contains_primary_color(self) -> None:
        profile = _make_full_profile()
        repo = _make_profile_repo([profile])

        cmd = GetCSSCommand(profile_repo=repo)
        css = await cmd.execute(profile.id)

        assert ":root {" in css
        assert "--color-primary: #1A1A1A;" in css

    async def test_get_css_missing_profile_raises(self) -> None:
        repo = _make_profile_repo()
        cmd = GetCSSCommand(profile_repo=repo)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(uuid.uuid4())


# ---------------------------------------------------------------------------
# GetTailwindCommand
# ---------------------------------------------------------------------------


class TestGetTailwindCommand:
    async def test_get_tailwind_returns_extend_dict(self) -> None:
        profile = _make_full_profile()
        repo = _make_profile_repo([profile])

        cmd = GetTailwindCommand(profile_repo=repo)
        theme = await cmd.execute(profile.id)

        assert "extend" in theme
        assert "colors" in theme["extend"]
        assert theme["extend"]["colors"]["primary"] == "#1A1A1A"

    async def test_get_tailwind_missing_profile_raises(self) -> None:
        repo = _make_profile_repo()
        cmd = GetTailwindCommand(profile_repo=repo)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(uuid.uuid4())
