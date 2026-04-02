"""Unit tests for media application commands."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from domains.media.application.commands import (
    CreateInfographicCommand,
    GenerateImageCommand,
    ListInfographicTemplatesQuery,
    SearchIconsCommand,
    SearchImagesCommand,
)
from domains.media.domain.entities import MediaAsset
from domains.media.domain.services import SVGInfographicService
from domains.media.domain.value_objects import AssetType

# ---------------------------------------------------------------------------
# Fake repos
# ---------------------------------------------------------------------------


def _make_asset_repo() -> AsyncMock:
    store: dict[uuid.UUID, MediaAsset] = {}
    repo = AsyncMock()

    async def save(asset: MediaAsset) -> None:
        store[asset.id] = asset

    async def get(asset_id: uuid.UUID) -> MediaAsset | None:
        return store.get(asset_id)

    async def list_all(limit: int = 50, offset: int = 0) -> list[MediaAsset]:
        items = list(store.values())
        return items[offset : offset + limit]

    async def delete(asset_id: uuid.UUID) -> None:
        store.pop(asset_id, None)

    repo.save = AsyncMock(side_effect=save)
    repo.get = AsyncMock(side_effect=get)
    repo.list_all = AsyncMock(side_effect=list_all)
    repo.delete = AsyncMock(side_effect=delete)
    return repo


def _make_template_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.list_all = AsyncMock(return_value=[])
    repo.get = AsyncMock(return_value=None)
    repo.save = AsyncMock()
    return repo


def _make_search_adapter(results: list[dict] | None = None) -> AsyncMock:
    adapter = AsyncMock()
    default = [
        {"url": "https://example.com/img1.jpg", "source": "pexels", "alt": "photo"},
        {"url": "https://example.com/img2.jpg", "source": "pexels", "alt": "photo2"},
    ]
    adapter.search = AsyncMock(return_value=default if results is None else results)
    return adapter


def _make_generation_adapter(url: str = "https://example.com/generated.jpg") -> AsyncMock:
    adapter = AsyncMock()
    adapter.generate = AsyncMock(return_value=url)
    return adapter


# ---------------------------------------------------------------------------
# SearchImagesCommand
# ---------------------------------------------------------------------------


class TestSearchImagesCommand:
    async def test_returns_list_of_dtos(self) -> None:
        cmd = SearchImagesCommand(
            repo=_make_asset_repo(),
            adapter=_make_search_adapter(),
        )
        results = await cmd.execute(query="cats", max_results=2)
        assert len(results) == 2
        assert all(r.type == AssetType.IMAGE.value for r in results)

    async def test_assets_saved_to_repo(self) -> None:
        repo = _make_asset_repo()
        cmd = SearchImagesCommand(repo=repo, adapter=_make_search_adapter())
        await cmd.execute(query="dogs", max_results=2)
        assert repo.save.call_count == 2

    async def test_source_override(self) -> None:
        cmd = SearchImagesCommand(
            repo=_make_asset_repo(),
            adapter=_make_search_adapter([{"url": "https://img.com/1.jpg", "source": "pexels"}]),
        )
        results = await cmd.execute(query="cars", source="pixabay")
        assert results[0].source == "pixabay"

    async def test_empty_results(self) -> None:
        cmd = SearchImagesCommand(
            repo=_make_asset_repo(),
            adapter=_make_search_adapter([]),
        )
        results = await cmd.execute(query="nothing")
        assert results == []


# ---------------------------------------------------------------------------
# GenerateImageCommand
# ---------------------------------------------------------------------------


class TestGenerateImageCommand:
    async def test_returns_dto(self) -> None:
        cmd = GenerateImageCommand(
            repo=_make_asset_repo(),
            adapter=_make_generation_adapter("https://ai.com/gen.jpg"),
        )
        result = await cmd.execute(prompt="a sunset over mountains")
        assert result.url == "https://ai.com/gen.jpg"
        assert result.type == AssetType.IMAGE.value
        assert result.metadata["prompt"] == "a sunset over mountains"

    async def test_asset_saved_to_repo(self) -> None:
        repo = _make_asset_repo()
        cmd = GenerateImageCommand(repo=repo, adapter=_make_generation_adapter())
        await cmd.execute(prompt="test")
        repo.save.assert_called_once()

    async def test_provider_stored_as_source(self) -> None:
        cmd = GenerateImageCommand(
            repo=_make_asset_repo(),
            adapter=_make_generation_adapter(),
        )
        result = await cmd.execute(prompt="test", provider="dalle")
        assert result.source == "dalle"

    async def test_default_size_in_metadata(self) -> None:
        cmd = GenerateImageCommand(
            repo=_make_asset_repo(),
            adapter=_make_generation_adapter(),
        )
        result = await cmd.execute(prompt="test")
        assert result.metadata["size"] == "1024x1024"


# ---------------------------------------------------------------------------
# CreateInfographicCommand
# ---------------------------------------------------------------------------


class TestCreateInfographicCommand:
    async def test_pie_chart_returns_svg_data_uri(self) -> None:
        cmd = CreateInfographicCommand(
            repo=_make_asset_repo(),
            template_repo=_make_template_repo(),
            svg_service=SVGInfographicService(),
        )
        result = await cmd.execute(
            infographic_type="pie_chart",
            data={
                "title": "Sales",
                "slices": [{"label": "A", "value": 60}, {"label": "B", "value": 40}],
            },
        )
        assert result.type == AssetType.INFOGRAPHIC.value
        assert result.url.startswith("data:image/svg+xml;base64,")
        assert result.source == "svg"

    async def test_bar_chart_returns_svg_data_uri(self) -> None:
        cmd = CreateInfographicCommand(
            repo=_make_asset_repo(),
            template_repo=_make_template_repo(),
        )
        result = await cmd.execute(
            infographic_type="bar_chart",
            data={"title": "Revenue", "bars": [{"label": "Q1", "value": 100}]},
        )
        assert result.url.startswith("data:image/svg+xml;base64,")

    async def test_metadata_contains_type_and_template(self) -> None:
        cmd = CreateInfographicCommand(
            repo=_make_asset_repo(),
            template_repo=_make_template_repo(),
        )
        result = await cmd.execute(
            infographic_type="timeline",
            data={"title": "T", "events": [{"label": "E1", "date": "2020"}]},
        )
        assert result.metadata["infographic_type"] == "timeline"
        assert "template_id" in result.metadata

    async def test_unknown_type_raises_value_error(self) -> None:
        cmd = CreateInfographicCommand(
            repo=_make_asset_repo(),
            template_repo=_make_template_repo(),
        )
        with pytest.raises(ValueError, match="Unknown infographic type"):
            await cmd.execute(infographic_type="nonexistent", data={})

    async def test_lookup_by_template_id(self) -> None:
        from domains.media.domain.services import BUILTIN_TEMPLATES_BY_NAME

        template = BUILTIN_TEMPLATES_BY_NAME["pie_chart"]
        cmd = CreateInfographicCommand(
            repo=_make_asset_repo(),
            template_repo=_make_template_repo(),
        )
        result = await cmd.execute(
            infographic_type="pie_chart",
            data={"title": "T", "slices": [{"label": "X", "value": 1}]},
            template_id=str(template.id),
        )
        assert result.url.startswith("data:image/svg+xml;base64,")

    async def test_invalid_template_id_raises(self) -> None:
        cmd = CreateInfographicCommand(
            repo=_make_asset_repo(),
            template_repo=_make_template_repo(),
        )
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(
                infographic_type="pie_chart",
                data={},
                template_id=str(uuid.uuid4()),
            )

    async def test_asset_saved_to_repo(self) -> None:
        repo = _make_asset_repo()
        cmd = CreateInfographicCommand(
            repo=repo,
            template_repo=_make_template_repo(),
        )
        await cmd.execute(
            infographic_type="comparison",
            data={
                "title": "Compare",
                "left_label": "A",
                "right_label": "B",
                "left_items": ["x"],
                "right_items": ["y"],
            },
        )
        repo.save.assert_called_once()


# ---------------------------------------------------------------------------
# SearchIconsCommand
# ---------------------------------------------------------------------------


class TestSearchIconsCommand:
    async def test_returns_icon_type_assets(self) -> None:
        cmd = SearchIconsCommand(
            repo=_make_asset_repo(),
            adapter=_make_search_adapter(
                [{"url": "https://icons.com/star.svg", "source": "iconify"}]
            ),
        )
        results = await cmd.execute(query="star")
        assert len(results) == 1
        assert results[0].type == AssetType.ICON.value

    async def test_query_is_prefixed_with_icon(self) -> None:
        adapter = _make_search_adapter([])
        cmd = SearchIconsCommand(repo=_make_asset_repo(), adapter=adapter)
        await cmd.execute(query="arrow")
        adapter.search.assert_called_once_with("icon arrow", 10)


# ---------------------------------------------------------------------------
# ListInfographicTemplatesQuery
# ---------------------------------------------------------------------------


class TestListInfographicTemplatesQuery:
    async def test_returns_five_builtin_templates(self) -> None:
        query = ListInfographicTemplatesQuery(template_repo=_make_template_repo())
        results = await query.execute()
        assert len(results) >= 5

    async def test_all_builtin_flag_set(self) -> None:
        query = ListInfographicTemplatesQuery(template_repo=_make_template_repo())
        results = await query.execute()
        builtin = [r for r in results if r.is_builtin]
        assert len(builtin) == 5

    async def test_custom_templates_included(self) -> None:
        from domains.media.domain.entities import InfographicTemplate

        custom = InfographicTemplate(
            id=uuid.uuid4(),
            name="custom_chart",
            svg_template="<svg/>",
            required_data_fields=["data"],
            is_builtin=False,
        )
        repo = _make_template_repo()
        repo.list_all = AsyncMock(return_value=[custom])
        query = ListInfographicTemplatesQuery(template_repo=repo)
        results = await query.execute()
        names = [r.name for r in results]
        assert "custom_chart" in names
