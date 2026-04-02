"""Style application queries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from domains.style.application.commands import _preset_to_dto, _profile_to_dto
from domains.style.application.dto import PresetDTO, StyleProfileDTO
from domains.style.domain.entities import BUILTIN_PRESETS
from domains.style.domain.repositories import StylePresetRepository, StyleProfileRepository


@dataclass
class GetStyleProfileQuery:
    repo: StyleProfileRepository

    async def execute(self, profile_id: uuid.UUID) -> StyleProfileDTO:
        profile = await self.repo.get(profile_id)
        if profile is None:
            raise ValueError(f"StyleProfile '{profile_id}' not found")
        return _profile_to_dto(profile)


@dataclass
class ListStyleProfilesQuery:
    repo: StyleProfileRepository

    async def execute(self, limit: int = 50, offset: int = 0) -> list[StyleProfileDTO]:
        profiles = await self.repo.list_all(limit=limit, offset=offset)
        return [_profile_to_dto(p) for p in profiles]


@dataclass
class ListPresetsQuery:
    preset_repo: StylePresetRepository

    async def execute(self, include_builtin: bool = True) -> list[PresetDTO]:
        """List all presets, optionally including built-in ones."""
        user_presets = await self.preset_repo.list_all()

        if include_builtin:
            builtin_dtos = [_preset_to_dto(p) for p in BUILTIN_PRESETS]
            return builtin_dtos + [_preset_to_dto(p) for p in user_presets]

        return [_preset_to_dto(p) for p in user_presets]


@dataclass
class GetPresetQuery:
    preset_repo: StylePresetRepository

    async def execute(self, preset_id: uuid.UUID) -> PresetDTO:
        # Check built-ins first
        for bp in BUILTIN_PRESETS:
            if bp.id == preset_id:
                return _preset_to_dto(bp)

        preset = await self.preset_repo.get(preset_id)
        if preset is None:
            raise ValueError(f"StylePreset '{preset_id}' not found")
        return _preset_to_dto(preset)
