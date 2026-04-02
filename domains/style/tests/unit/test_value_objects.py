"""Unit tests for style domain value objects."""

from __future__ import annotations

import pytest

from domains.style.domain.value_objects import ColorPalette, LayoutRules, Spacing, Typography


class TestColorPalette:
    def _make(self) -> ColorPalette:
        return ColorPalette(
            primary="#1A1A1A",
            secondary="#555555",
            accent=("#0066CC",),
            background="#FFFFFF",
            text="#1A1A1A",
        )

    def test_create_valid(self) -> None:
        palette = self._make()
        assert palette.primary == "#1A1A1A"
        assert palette.background == "#FFFFFF"
        assert len(palette.accent) == 1

    def test_hex_is_uppercased(self) -> None:
        palette = ColorPalette(
            primary="#aabbcc",
            secondary="#ddeeff",
            accent=("#112233",),
            background="#ffffff",
            text="#000000",
        )
        assert palette.primary == "#AABBCC"

    def test_invalid_hex_raises(self) -> None:
        with pytest.raises(ValueError, match="primary"):
            ColorPalette(
                primary="red",
                secondary="#555555",
                accent=(),
                background="#FFFFFF",
                text="#000000",
            )

    def test_too_many_accents_raises(self) -> None:
        with pytest.raises(ValueError, match="accent"):
            ColorPalette(
                primary="#000000",
                secondary="#111111",
                accent=("#AA0000", "#BB0000", "#CC0000", "#DD0000", "#EE0000", "#FF0000"),
                background="#FFFFFF",
                text="#000000",
            )

    def test_equality(self) -> None:
        p1 = self._make()
        p2 = self._make()
        assert p1 == p2

    def test_inequality_on_primary(self) -> None:
        p1 = self._make()
        p2 = ColorPalette(
            primary="#FF0000",
            secondary="#555555",
            accent=("#0066CC",),
            background="#FFFFFF",
            text="#1A1A1A",
        )
        assert p1 != p2

    def test_hashable(self) -> None:
        p = self._make()
        assert hash(p) == hash(p)
        s = {p, self._make()}
        assert len(s) == 1


class TestTypography:
    def _make(self) -> Typography:
        return Typography.from_sizes_dict(
            heading_font="Inter",
            body_font="Inter",
            sizes={"h1": "36px", "h2": "28px", "h3": "22px", "body": "16px"},
        )

    def test_create(self) -> None:
        t = self._make()
        assert t.heading_font == "Inter"
        assert t.sizes_dict["h1"] == "36px"

    def test_sizes_dict_roundtrip(self) -> None:
        sizes = {"h1": "40px", "body": "16px"}
        t = Typography.from_sizes_dict("Roboto", "Lato", sizes)
        assert t.sizes_dict == sizes

    def test_equality(self) -> None:
        t1 = self._make()
        t2 = self._make()
        assert t1 == t2

    def test_inequality_on_font(self) -> None:
        t1 = self._make()
        t2 = Typography.from_sizes_dict(
            heading_font="Roboto",
            body_font="Inter",
            sizes={"h1": "36px", "h2": "28px", "h3": "22px", "body": "16px"},
        )
        assert t1 != t2

    def test_hashable(self) -> None:
        t = self._make()
        assert hash(t) == hash(t)


class TestLayoutRules:
    def _make(self) -> LayoutRules:
        return LayoutRules(
            margin="40px",
            padding="24px",
            alignment_grid=12,
            max_content_width="1200px",
        )

    def test_create(self) -> None:
        lo = self._make()
        assert lo.alignment_grid == 12

    def test_invalid_grid_raises(self) -> None:
        with pytest.raises(ValueError, match="alignment_grid"):
            LayoutRules(margin="40px", padding="24px", alignment_grid=0, max_content_width="1200px")

    def test_equality(self) -> None:
        assert self._make() == self._make()

    def test_hashable(self) -> None:
        lo = self._make()
        assert hash(lo) == hash(lo)


class TestSpacing:
    def _make(self) -> Spacing:
        return Spacing(line_height="1.5", paragraph_gap="20px", element_gap="16px")

    def test_create(self) -> None:
        sp = self._make()
        assert sp.line_height == "1.5"

    def test_equality(self) -> None:
        assert self._make() == self._make()

    def test_inequality(self) -> None:
        s1 = self._make()
        s2 = Spacing(line_height="2.0", paragraph_gap="20px", element_gap="16px")
        assert s1 != s2

    def test_hashable(self) -> None:
        sp = self._make()
        assert hash(sp) == hash(sp)
