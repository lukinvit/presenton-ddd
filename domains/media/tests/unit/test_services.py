"""Unit tests for SVGInfographicService and built-in templates."""

from __future__ import annotations

import uuid

from domains.media.domain.services import (
    BUILTIN_TEMPLATE_IDS,
    BUILTIN_TEMPLATES,
    BUILTIN_TEMPLATES_BY_ID,
    BUILTIN_TEMPLATES_BY_NAME,
    SVGInfographicService,
)
from domains.media.domain.value_objects import InfographicType


class TestBuiltinTemplates:
    def test_five_builtin_templates(self) -> None:
        assert len(BUILTIN_TEMPLATES) == 5

    def test_all_types_present(self) -> None:
        names = {t.name for t in BUILTIN_TEMPLATES}
        expected = {it.value for it in InfographicType}
        assert names == expected

    def test_all_templates_are_builtin(self) -> None:
        assert all(t.is_builtin for t in BUILTIN_TEMPLATES)

    def test_deterministic_ids(self) -> None:
        """IDs must be stable across calls (UUID5)."""
        for itype in InfographicType:
            tid = BUILTIN_TEMPLATE_IDS[itype.value]
            assert isinstance(tid, uuid.UUID)
            # Recompute
            import uuid as _uuid

            ns = _uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
            expected = _uuid.uuid5(ns, f"media:template:{itype.value}")
            assert tid == expected

    def test_lookup_by_id(self) -> None:
        for t in BUILTIN_TEMPLATES:
            assert BUILTIN_TEMPLATES_BY_ID[t.id] is t

    def test_lookup_by_name(self) -> None:
        for t in BUILTIN_TEMPLATES:
            assert BUILTIN_TEMPLATES_BY_NAME[t.name] is t

    def test_templates_have_required_fields(self) -> None:
        for t in BUILTIN_TEMPLATES:
            assert len(t.required_data_fields) > 0

    def test_templates_have_svg_content(self) -> None:
        for t in BUILTIN_TEMPLATES:
            assert "<svg" in t.svg_template


class TestSVGInfographicServicePieChart:
    def setup_method(self) -> None:
        self.svc = SVGInfographicService()

    def test_returns_svg_string(self) -> None:
        data = {
            "title": "Sales",
            "slices": [
                {"label": "Q1", "value": 30},
                {"label": "Q2", "value": 70},
            ],
        }
        svg = self.svc.create_pie_chart(data)
        assert svg.startswith("<svg")
        assert "</svg>" in svg

    def test_contains_title(self) -> None:
        data = {"title": "My Pie", "slices": [{"label": "A", "value": 1}]}
        svg = self.svc.create_pie_chart(data)
        assert "My Pie" in svg

    def test_contains_slice_labels(self) -> None:
        data = {
            "title": "T",
            "slices": [
                {"label": "Alpha", "value": 50},
                {"label": "Beta", "value": 50},
            ],
        }
        svg = self.svc.create_pie_chart(data)
        assert "Alpha" in svg
        assert "Beta" in svg

    def test_empty_slices_does_not_crash(self) -> None:
        data = {"title": "Empty", "slices": []}
        svg = self.svc.create_pie_chart(data)
        assert "<svg" in svg

    def test_custom_size(self) -> None:
        data = {"title": "T", "slices": [], "width": 600, "height": 600}
        svg = self.svc.create_pie_chart(data)
        assert 'width="600"' in svg
        assert 'height="600"' in svg

    def test_single_slice_full_circle(self) -> None:
        data = {"title": "T", "slices": [{"label": "All", "value": 100}]}
        svg = self.svc.create_pie_chart(data)
        assert "All" in svg


class TestSVGInfographicServiceBarChart:
    def setup_method(self) -> None:
        self.svc = SVGInfographicService()

    def test_returns_svg_string(self) -> None:
        data = {
            "title": "Revenue",
            "bars": [
                {"label": "Jan", "value": 100},
                {"label": "Feb", "value": 200},
            ],
        }
        svg = self.svc.create_bar_chart(data)
        assert svg.startswith("<svg")
        assert "</svg>" in svg

    def test_contains_title(self) -> None:
        data = {"title": "Revenue Chart", "bars": [{"label": "A", "value": 10}]}
        svg = self.svc.create_bar_chart(data)
        assert "Revenue Chart" in svg

    def test_contains_labels(self) -> None:
        data = {
            "title": "T",
            "bars": [
                {"label": "January", "value": 50},
                {"label": "February", "value": 80},
            ],
        }
        svg = self.svc.create_bar_chart(data)
        assert "January" in svg
        assert "February" in svg

    def test_empty_bars_does_not_crash(self) -> None:
        data = {"title": "Empty", "bars": []}
        svg = self.svc.create_bar_chart(data)
        assert "<svg" in svg

    def test_custom_dimensions(self) -> None:
        data = {"title": "T", "bars": [], "width": 800, "height": 500}
        svg = self.svc.create_bar_chart(data)
        assert 'width="800"' in svg
        assert 'height="500"' in svg


class TestSVGInfographicServiceCreateFromTemplate:
    def setup_method(self) -> None:
        self.svc = SVGInfographicService()

    def test_pie_chart_via_template(self) -> None:
        template = BUILTIN_TEMPLATES_BY_NAME["pie_chart"]
        data = {"title": "T", "slices": [{"label": "A", "value": 1}]}
        svg = self.svc.create_from_template(template, data)
        assert "<svg" in svg

    def test_bar_chart_via_template(self) -> None:
        template = BUILTIN_TEMPLATES_BY_NAME["bar_chart"]
        data = {"title": "T", "bars": [{"label": "X", "value": 5}]}
        svg = self.svc.create_from_template(template, data)
        assert "<svg" in svg

    def test_timeline_via_template(self) -> None:
        template = BUILTIN_TEMPLATES_BY_NAME["timeline"]
        data = {
            "title": "History",
            "events": [
                {"label": "Start", "date": "2020"},
                {"label": "End", "date": "2024"},
            ],
        }
        svg = self.svc.create_from_template(template, data)
        assert "<svg" in svg
        assert "History" in svg
        assert "Start" in svg

    def test_flowchart_via_template(self) -> None:
        template = BUILTIN_TEMPLATES_BY_NAME["flowchart"]
        data = {
            "title": "Process",
            "nodes": [
                {"label": "Step 1"},
                {"label": "Step 2"},
                {"label": "Step 3"},
            ],
        }
        svg = self.svc.create_from_template(template, data)
        assert "<svg" in svg
        assert "Step 1" in svg
        assert "arrowhead" in svg

    def test_comparison_via_template(self) -> None:
        template = BUILTIN_TEMPLATES_BY_NAME["comparison"]
        data = {
            "title": "A vs B",
            "left_label": "Option A",
            "right_label": "Option B",
            "left_items": ["Fast", "Cheap"],
            "right_items": ["Slow", "Expensive"],
        }
        svg = self.svc.create_from_template(template, data)
        assert "<svg" in svg
        assert "Option A" in svg
        assert "Option B" in svg
        assert "Fast" in svg
