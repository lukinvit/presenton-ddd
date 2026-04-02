"""FastAPI router for the media domain."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from domains.media.api.schemas import (
    CreateInfographicRequest,
    GenerateImageRequest,
    InfographicTemplateResponse,
    MediaAssetResponse,
    SearchIconsRequest,
    SearchImagesRequest,
)
from domains.media.application.commands import (
    CreateInfographicCommand,
    GenerateImageCommand,
    ListInfographicTemplatesQuery,
    SearchIconsCommand,
    SearchImagesCommand,
)
from domains.media.application.dto import InfographicTemplateDTO, MediaAssetDTO
from domains.media.domain.adapters import ImageGenerationAdapter, ImageSearchAdapter
from domains.media.domain.repositories import InfographicTemplateRepository, MediaAssetRepository
from domains.media.domain.services import SVGInfographicService

# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _asset_dto_to_response(dto: MediaAssetDTO) -> MediaAssetResponse:
    return MediaAssetResponse(
        id=dto.id,
        type=dto.type,
        url=dto.url,
        source=dto.source,
        metadata=dto.metadata,
        created_at=dto.created_at,
    )


def _template_dto_to_response(dto: InfographicTemplateDTO) -> InfographicTemplateResponse:
    return InfographicTemplateResponse(
        id=dto.id,
        name=dto.name,
        required_data_fields=dto.required_data_fields,
        is_builtin=dto.is_builtin,
    )


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------


def create_media_router(
    asset_repo: MediaAssetRepository,
    template_repo: InfographicTemplateRepository,
    image_search_adapter: ImageSearchAdapter,
    image_generation_adapter: ImageGenerationAdapter,
    svg_service: SVGInfographicService | None = None,
) -> APIRouter:
    router = APIRouter(tags=["media"])

    _svg_service = svg_service or SVGInfographicService()

    @router.post("/media/search", response_model=list[MediaAssetResponse])
    async def search_images(req: SearchImagesRequest) -> list[MediaAssetResponse]:
        cmd = SearchImagesCommand(repo=asset_repo, adapter=image_search_adapter)
        try:
            results = await cmd.execute(
                query=req.query,
                max_results=req.max_results,
                source=req.source,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e)) from e
        return [_asset_dto_to_response(r) for r in results]

    @router.post("/media/generate", response_model=MediaAssetResponse, status_code=201)
    async def generate_image(req: GenerateImageRequest) -> MediaAssetResponse:
        cmd = GenerateImageCommand(repo=asset_repo, adapter=image_generation_adapter)
        try:
            result = await cmd.execute(
                prompt=req.prompt,
                provider=req.provider,
                size=req.size,
            )
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e)) from e
        return _asset_dto_to_response(result)

    @router.post("/media/infographic", response_model=MediaAssetResponse, status_code=201)
    async def create_infographic(req: CreateInfographicRequest) -> MediaAssetResponse:
        cmd = CreateInfographicCommand(
            repo=asset_repo,
            template_repo=template_repo,
            svg_service=_svg_service,
        )
        try:
            result = await cmd.execute(
                infographic_type=req.type,
                data=req.data,
                template_id=req.template_id,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return _asset_dto_to_response(result)

    @router.get("/media/infographic-templates", response_model=list[InfographicTemplateResponse])
    async def list_infographic_templates() -> list[InfographicTemplateResponse]:
        query = ListInfographicTemplatesQuery(template_repo=template_repo)
        results = await query.execute()
        return [_template_dto_to_response(r) for r in results]

    @router.post("/media/icons/search", response_model=list[MediaAssetResponse])
    async def search_icons(req: SearchIconsRequest) -> list[MediaAssetResponse]:
        cmd = SearchIconsCommand(repo=asset_repo, adapter=image_search_adapter)
        try:
            results = await cmd.execute(query=req.query, max_results=req.max_results)
        except Exception as e:
            raise HTTPException(status_code=502, detail=str(e)) from e
        return [_asset_dto_to_response(r) for r in results]

    return router
