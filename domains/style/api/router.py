"""FastAPI router for the style domain."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from domains.style.api.schemas import (
    ColorPaletteResponse,
    CreatePresetRequest,
    CSSResponse,
    ExtractFromFileRequest,
    ExtractFromURLRequest,
    LayoutRulesResponse,
    PresetResponse,
    SpacingResponse,
    StyleProfileResponse,
    TailwindResponse,
    TypographyResponse,
    ValidateStyleRequest,
    ValidationCriterionResponse,
    ValidationResultResponse,
)
from domains.style.application.commands import (
    ApplyStyleCommand,
    CreatePresetCommand,
    ExtractStyleFromFileCommand,
    ExtractStyleFromURLCommand,
    GetCSSCommand,
    GetTailwindCommand,
    ValidateStyleCommand,
)
from domains.style.application.dto import PresetDTO, StyleProfileDTO
from domains.style.application.queries import (
    GetStyleProfileQuery,
    ListPresetsQuery,
)
from domains.style.domain.repositories import StylePresetRepository, StyleProfileRepository
from shared.domain.events import EventBus

# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _dto_to_profile_response(dto: StyleProfileDTO) -> StyleProfileResponse:
    return StyleProfileResponse(
        id=dto.id,
        name=dto.name,
        source=dto.source,
        created_at=dto.created_at,
        colors=(
            ColorPaletteResponse(
                primary=dto.colors.primary,
                secondary=dto.colors.secondary,
                accent=dto.colors.accent,
                background=dto.colors.background,
                text=dto.colors.text,
            )
            if dto.colors
            else None
        ),
        typography=(
            TypographyResponse(
                heading_font=dto.typography.heading_font,
                body_font=dto.typography.body_font,
                sizes=dto.typography.sizes,
            )
            if dto.typography
            else None
        ),
        layout=(
            LayoutRulesResponse(
                margin=dto.layout.margin,
                padding=dto.layout.padding,
                alignment_grid=dto.layout.alignment_grid,
                max_content_width=dto.layout.max_content_width,
            )
            if dto.layout
            else None
        ),
        spacing=(
            SpacingResponse(
                line_height=dto.spacing.line_height,
                paragraph_gap=dto.spacing.paragraph_gap,
                element_gap=dto.spacing.element_gap,
            )
            if dto.spacing
            else None
        ),
    )


def _dto_to_preset_response(dto: PresetDTO) -> PresetResponse:
    return PresetResponse(
        id=dto.id,
        name=dto.name,
        description=dto.description,
        is_builtin=dto.is_builtin,
        profile=_dto_to_profile_response(dto.profile) if dto.profile else None,
    )


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------


def create_style_router(
    profile_repo: StyleProfileRepository,
    preset_repo: StylePresetRepository,
    event_bus: EventBus,
) -> APIRouter:
    router = APIRouter(tags=["styles"])

    # ------------------------------------------------------------------
    # Static-path routes MUST come before /{profile_id} parameterised
    # routes to avoid FastAPI matching "presets" as a UUID parameter.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Extract from file
    # ------------------------------------------------------------------

    @router.post("/styles/extract-from-file", response_model=StyleProfileResponse, status_code=201)
    async def extract_from_file(req: ExtractFromFileRequest) -> StyleProfileResponse:
        cmd = ExtractStyleFromFileCommand(repo=profile_repo, event_bus=event_bus)
        try:
            result = await cmd.execute(file_path=req.file_path, name=req.name)
        except (FileNotFoundError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _dto_to_profile_response(result)

    # ------------------------------------------------------------------
    # Extract from URL
    # ------------------------------------------------------------------

    @router.post("/styles/extract-from-url", response_model=StyleProfileResponse, status_code=201)
    async def extract_from_url(req: ExtractFromURLRequest) -> StyleProfileResponse:
        cmd = ExtractStyleFromURLCommand(repo=profile_repo, event_bus=event_bus)
        try:
            result = await cmd.execute(url=req.url, name=req.name)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _dto_to_profile_response(result)

    # ------------------------------------------------------------------
    # Presets (static paths — must be before /{profile_id})
    # ------------------------------------------------------------------

    @router.get("/styles/presets", response_model=list[PresetResponse])
    async def list_presets() -> list[PresetResponse]:
        query = ListPresetsQuery(preset_repo=preset_repo)
        results = await query.execute(include_builtin=True)
        return [_dto_to_preset_response(r) for r in results]

    @router.post("/styles/presets", response_model=PresetResponse, status_code=201)
    async def create_preset(req: CreatePresetRequest) -> PresetResponse:
        cmd = CreatePresetCommand(
            profile_repo=profile_repo,
            preset_repo=preset_repo,
            event_bus=event_bus,
        )
        try:
            result = await cmd.execute(
                name=req.name,
                description=req.description,
                profile_id=req.profile_id,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _dto_to_preset_response(result)

    # ------------------------------------------------------------------
    # Get a style profile (parameterised — must follow static paths)
    # ------------------------------------------------------------------

    @router.get("/styles/{profile_id}", response_model=StyleProfileResponse)
    async def get_style_profile(profile_id: uuid.UUID) -> StyleProfileResponse:
        query = GetStyleProfileQuery(repo=profile_repo)
        try:
            result = await query.execute(profile_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return _dto_to_profile_response(result)

    # ------------------------------------------------------------------
    # Apply style to presentation
    # ------------------------------------------------------------------

    @router.post("/styles/{profile_id}/apply/{presentation_id}", status_code=200)
    async def apply_style(profile_id: uuid.UUID, presentation_id: uuid.UUID) -> dict[str, str]:
        cmd = ApplyStyleCommand(profile_repo=profile_repo, event_bus=event_bus)
        try:
            await cmd.execute(presentation_id=presentation_id, profile_id=profile_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return {"status": "ok"}

    # ------------------------------------------------------------------
    # Validate style
    # ------------------------------------------------------------------

    @router.post("/styles/{profile_id}/validate", response_model=ValidationResultResponse)
    async def validate_style(
        profile_id: uuid.UUID, req: ValidateStyleRequest
    ) -> ValidationResultResponse:
        cmd = ValidateStyleCommand(profile_repo=profile_repo)
        rendered_data = {
            "colors": req.colors,
            "fonts": req.fonts,
            "bg_color": req.bg_color,
        }
        try:
            result = await cmd.execute(profile_id=profile_id, rendered_data=rendered_data)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        criteria = [
            ValidationCriterionResponse(
                criterion=c["criterion"],
                passed=c["passed"],
                details=c["details"],
            )
            for c in result.criteria
        ]
        return ValidationResultResponse(
            profile_id=result.profile_id,
            passed=result.passed,
            criteria=criteria,
        )

    # ------------------------------------------------------------------
    # CSS / Tailwind export
    # ------------------------------------------------------------------

    @router.get("/styles/{profile_id}/css", response_model=CSSResponse)
    async def get_css(profile_id: uuid.UUID) -> CSSResponse:
        cmd = GetCSSCommand(profile_repo=profile_repo)
        try:
            css = await cmd.execute(profile_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return CSSResponse(profile_id=str(profile_id), css=css)

    @router.get("/styles/{profile_id}/tailwind", response_model=TailwindResponse)
    async def get_tailwind(profile_id: uuid.UUID) -> TailwindResponse:
        cmd = GetTailwindCommand(profile_repo=profile_repo)
        try:
            theme = await cmd.execute(profile_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return TailwindResponse(profile_id=str(profile_id), theme=theme)

    return router
