"""Media application commands."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from domains.media.application.dto import InfographicTemplateDTO, MediaAssetDTO
from domains.media.domain.adapters import ImageGenerationAdapter, ImageSearchAdapter
from domains.media.domain.entities import InfographicTemplate, MediaAsset
from domains.media.domain.repositories import InfographicTemplateRepository, MediaAssetRepository
from domains.media.domain.services import (
    BUILTIN_TEMPLATES,
    BUILTIN_TEMPLATES_BY_ID,
    BUILTIN_TEMPLATES_BY_NAME,
    SVGInfographicService,
)
from domains.media.domain.value_objects import AssetType, InfographicType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _asset_to_dto(asset: MediaAsset) -> MediaAssetDTO:
    return MediaAssetDTO(
        id=str(asset.id),
        type=asset.type.value,
        url=asset.url,
        source=asset.source,
        metadata=asset.metadata,
        created_at=asset.created_at.isoformat(),
    )


def _template_to_dto(template: InfographicTemplate) -> InfographicTemplateDTO:
    return InfographicTemplateDTO(
        id=str(template.id),
        name=template.name,
        required_data_fields=list(template.required_data_fields),
        is_builtin=template.is_builtin,
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@dataclass
class SearchImagesCommand:
    """Search for images using an external adapter."""

    repo: MediaAssetRepository
    adapter: ImageSearchAdapter

    async def execute(
        self,
        query: str,
        max_results: int = 10,
        source: str | None = None,
    ) -> list[MediaAssetDTO]:
        raw_results = await self.adapter.search(query, max_results)
        assets: list[MediaAssetDTO] = []
        for item in raw_results:
            asset = MediaAsset(
                id=uuid.uuid4(),
                type=AssetType.IMAGE,
                url=item.get("url", ""),
                source=source or item.get("source", "unknown"),
                metadata={k: v for k, v in item.items() if k not in {"url", "source"}},
            )
            await self.repo.save(asset)
            assets.append(_asset_to_dto(asset))
        return assets


@dataclass
class GenerateImageCommand:
    """Generate an image using an AI provider adapter."""

    repo: MediaAssetRepository
    adapter: ImageGenerationAdapter

    async def execute(
        self,
        prompt: str,
        provider: str | None = None,
        size: str = "1024x1024",
    ) -> MediaAssetDTO:
        url = await self.adapter.generate(prompt, size)
        asset = MediaAsset(
            id=uuid.uuid4(),
            type=AssetType.IMAGE,
            url=url,
            source=provider or "ai",
            metadata={"prompt": prompt, "size": size},
        )
        await self.repo.save(asset)
        return _asset_to_dto(asset)


@dataclass
class CreateInfographicCommand:
    """Create an infographic SVG from a template or by type."""

    repo: MediaAssetRepository
    template_repo: InfographicTemplateRepository
    svg_service: SVGInfographicService | None = None

    def __post_init__(self) -> None:
        if self.svg_service is None:
            self.svg_service = SVGInfographicService()

    async def execute(
        self,
        infographic_type: str,
        data: dict[str, Any],
        template_id: str | None = None,
    ) -> MediaAssetDTO:
        # Resolve template
        template: InfographicTemplate | None = None
        if template_id is not None:
            tid = uuid.UUID(template_id)
            template = BUILTIN_TEMPLATES_BY_ID.get(tid)
            if template is None:
                template = await self.template_repo.get(tid)
            if template is None:
                raise ValueError(f"Template '{template_id}' not found")
        else:
            template = BUILTIN_TEMPLATES_BY_NAME.get(infographic_type)
            if template is None:
                try:
                    InfographicType(infographic_type)
                except ValueError as exc:
                    raise ValueError(f"Unknown infographic type: '{infographic_type}'") from exc
                template = BUILTIN_TEMPLATES_BY_NAME.get(infographic_type)

        if template is None:
            raise ValueError(f"No template found for type '{infographic_type}'")

        svg_content = self.svg_service.create_from_template(template, data)  # type: ignore[union-attr]

        # Embed SVG as data URI so it is a proper URL-like string
        import base64

        encoded = base64.b64encode(svg_content.encode()).decode()
        url = f"data:image/svg+xml;base64,{encoded}"

        asset = MediaAsset(
            id=uuid.uuid4(),
            type=AssetType.INFOGRAPHIC,
            url=url,
            source="svg",
            metadata={
                "infographic_type": infographic_type,
                "template_id": str(template.id),
                "template_name": template.name,
            },
        )
        await self.repo.save(asset)
        return _asset_to_dto(asset)


@dataclass
class SearchIconsCommand:
    """Search for icons using an image search adapter with an icon-biased query."""

    repo: MediaAssetRepository
    adapter: ImageSearchAdapter

    async def execute(self, query: str, max_results: int = 10) -> list[MediaAssetDTO]:
        raw_results = await self.adapter.search(f"icon {query}", max_results)
        assets: list[MediaAssetDTO] = []
        for item in raw_results:
            asset = MediaAsset(
                id=uuid.uuid4(),
                type=AssetType.ICON,
                url=item.get("url", ""),
                source=item.get("source", "unknown"),
                metadata={k: v for k, v in item.items() if k not in {"url", "source"}},
            )
            await self.repo.save(asset)
            assets.append(_asset_to_dto(asset))
        return assets


# ---------------------------------------------------------------------------
# Query: list infographic templates
# ---------------------------------------------------------------------------


@dataclass
class ListInfographicTemplatesQuery:
    """Return all known infographic templates (built-in + custom)."""

    template_repo: InfographicTemplateRepository

    async def execute(self) -> list[InfographicTemplateDTO]:
        # Start with built-ins
        templates = list(BUILTIN_TEMPLATES)
        # Add custom ones from repo
        custom = await self.template_repo.list_all()
        # Avoid duplicates by id
        builtin_ids = {t.id for t in templates}
        templates.extend(t for t in custom if t.id not in builtin_ids)
        return [_template_to_dto(t) for t in templates]
