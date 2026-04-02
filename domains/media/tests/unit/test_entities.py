"""Unit tests for media domain entities and value objects."""

from __future__ import annotations

import uuid

from domains.media.domain.entities import InfographicTemplate, MediaAsset
from domains.media.domain.value_objects import AssetType, InfographicType


class TestAssetType:
    def test_all_values(self) -> None:
        assert AssetType.IMAGE.value == "image"
        assert AssetType.INFOGRAPHIC.value == "infographic"
        assert AssetType.ICON.value == "icon"


class TestInfographicType:
    def test_all_values(self) -> None:
        assert InfographicType.PIE_CHART.value == "pie_chart"
        assert InfographicType.BAR_CHART.value == "bar_chart"
        assert InfographicType.TIMELINE.value == "timeline"
        assert InfographicType.FLOWCHART.value == "flowchart"
        assert InfographicType.COMPARISON.value == "comparison"


class TestMediaAsset:
    def test_create_image_asset(self) -> None:
        asset = MediaAsset(
            id=uuid.uuid4(),
            type=AssetType.IMAGE,
            url="https://example.com/photo.jpg",
            source="pexels",
            metadata={"width": 1920, "height": 1080},
        )
        assert asset.type == AssetType.IMAGE
        assert asset.source == "pexels"
        assert asset.metadata["width"] == 1920

    def test_create_infographic_asset(self) -> None:
        asset = MediaAsset(
            id=uuid.uuid4(),
            type=AssetType.INFOGRAPHIC,
            url="data:image/svg+xml;base64,abc",
            source="svg",
        )
        assert asset.type == AssetType.INFOGRAPHIC
        assert asset.source == "svg"

    def test_create_icon_asset(self) -> None:
        asset = MediaAsset(
            id=uuid.uuid4(),
            type=AssetType.ICON,
            url="https://example.com/icon.svg",
            source="pixabay",
        )
        assert asset.type == AssetType.ICON

    def test_asset_with_same_id_and_fields_are_equal(self) -> None:
        aid = uuid.uuid4()
        from datetime import UTC, datetime

        ts = datetime.now(UTC)
        a1 = MediaAsset(
            id=aid, type=AssetType.IMAGE, url="https://a.com/img.jpg", source="test", created_at=ts
        )
        a2 = MediaAsset(
            id=aid, type=AssetType.IMAGE, url="https://a.com/img.jpg", source="test", created_at=ts
        )
        assert a1 == a2

    def test_asset_with_different_id_are_not_equal(self) -> None:
        from datetime import UTC, datetime

        ts = datetime.now(UTC)
        a1 = MediaAsset(
            id=uuid.uuid4(),
            type=AssetType.IMAGE,
            url="https://a.com/img.jpg",
            source="test",
            created_at=ts,
        )
        a2 = MediaAsset(
            id=uuid.uuid4(),
            type=AssetType.IMAGE,
            url="https://a.com/img.jpg",
            source="test",
            created_at=ts,
        )
        assert a1 != a2

    def test_created_at_set_automatically(self) -> None:
        asset = MediaAsset(id=uuid.uuid4(), type=AssetType.IMAGE, url="u", source="s")
        assert asset.created_at is not None


class TestInfographicTemplate:
    def test_create_template(self) -> None:
        t = InfographicTemplate(
            id=uuid.uuid4(),
            name="pie_chart",
            svg_template="<svg>{slices}</svg>",
            required_data_fields=["title", "slices"],
            is_builtin=True,
        )
        assert t.name == "pie_chart"
        assert "slices" in t.required_data_fields
        assert t.is_builtin is True

    def test_template_with_same_fields_are_equal(self) -> None:
        tid = uuid.uuid4()
        t1 = InfographicTemplate(
            id=tid, name="pie_chart", svg_template="<svg/>", required_data_fields=[]
        )
        t2 = InfographicTemplate(
            id=tid, name="pie_chart", svg_template="<svg/>", required_data_fields=[]
        )
        assert t1 == t2

    def test_template_with_different_id_are_not_equal(self) -> None:
        t1 = InfographicTemplate(
            id=uuid.uuid4(), name="pie_chart", svg_template="<svg/>", required_data_fields=[]
        )
        t2 = InfographicTemplate(
            id=uuid.uuid4(), name="pie_chart", svg_template="<svg/>", required_data_fields=[]
        )
        assert t1 != t2
