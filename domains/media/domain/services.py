"""Media domain services."""

from __future__ import annotations

import math
import uuid
from typing import Any

from .entities import InfographicTemplate
from .value_objects import InfographicType

# ---------------------------------------------------------------------------
# Deterministic UUID5 IDs for built-in templates
# ---------------------------------------------------------------------------

_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # uuid.NAMESPACE_URL

BUILTIN_TEMPLATE_IDS: dict[str, uuid.UUID] = {
    InfographicType.PIE_CHART.value: uuid.uuid5(_NAMESPACE, "media:template:pie_chart"),
    InfographicType.BAR_CHART.value: uuid.uuid5(_NAMESPACE, "media:template:bar_chart"),
    InfographicType.TIMELINE.value: uuid.uuid5(_NAMESPACE, "media:template:timeline"),
    InfographicType.FLOWCHART.value: uuid.uuid5(_NAMESPACE, "media:template:flowchart"),
    InfographicType.COMPARISON.value: uuid.uuid5(_NAMESPACE, "media:template:comparison"),
}

# ---------------------------------------------------------------------------
# SVG template strings with {placeholder} syntax
# ---------------------------------------------------------------------------

_PIE_CHART_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <title>{title}</title>
  <!-- slices rendered by SVGInfographicService.create_from_template -->
  {slices}
  <text x="{cx}" y="{cy}" text-anchor="middle" font-size="14" fill="{text_color}">{title}</text>
  {legend}
</svg>"""

_BAR_CHART_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <title>{title}</title>
  <!-- bars rendered by SVGInfographicService.create_from_template -->
  {bars}
  <line x1="{margin}" y1="{chart_bottom}" x2="{chart_right}" y2="{chart_bottom}" stroke="{axis_color}" stroke-width="2"/>
  <text x="{title_x}" y="{title_y}" text-anchor="middle" font-size="16" fill="{text_color}">{title}</text>
</svg>"""

_TIMELINE_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <title>{title}</title>
  <line x1="{axis_x}" y1="{axis_start_y}" x2="{axis_x}" y2="{axis_end_y}" stroke="{axis_color}" stroke-width="3"/>
  {events}
  <text x="{title_x}" y="30" text-anchor="middle" font-size="16" fill="{text_color}">{title}</text>
</svg>"""

_FLOWCHART_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <title>{title}</title>
  {nodes}
  {arrows}
  <text x="{title_x}" y="30" text-anchor="middle" font-size="16" fill="{text_color}">{title}</text>
</svg>"""

_COMPARISON_TEMPLATE = """\
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <title>{title}</title>
  <rect x="0" y="0" width="{half_width}" height="{height}" fill="{left_bg}"/>
  <rect x="{half_width}" y="0" width="{half_width}" height="{height}" fill="{right_bg}"/>
  <text x="{left_cx}" y="{header_y}" text-anchor="middle" font-size="18" fill="{header_color}" font-weight="bold">{left_label}</text>
  <text x="{right_cx}" y="{header_y}" text-anchor="middle" font-size="18" fill="{header_color}" font-weight="bold">{right_label}</text>
  {left_items}
  {right_items}
  <text x="{title_x}" y="24" text-anchor="middle" font-size="16" fill="{text_color}" font-weight="bold">{title}</text>
</svg>"""


# ---------------------------------------------------------------------------
# Built-in template objects
# ---------------------------------------------------------------------------


def _make_builtin_templates() -> list[InfographicTemplate]:
    return [
        InfographicTemplate(
            id=BUILTIN_TEMPLATE_IDS[InfographicType.PIE_CHART.value],
            name="pie_chart",
            svg_template=_PIE_CHART_TEMPLATE,
            required_data_fields=["title", "slices"],
            is_builtin=True,
        ),
        InfographicTemplate(
            id=BUILTIN_TEMPLATE_IDS[InfographicType.BAR_CHART.value],
            name="bar_chart",
            svg_template=_BAR_CHART_TEMPLATE,
            required_data_fields=["title", "bars"],
            is_builtin=True,
        ),
        InfographicTemplate(
            id=BUILTIN_TEMPLATE_IDS[InfographicType.TIMELINE.value],
            name="timeline",
            svg_template=_TIMELINE_TEMPLATE,
            required_data_fields=["title", "events"],
            is_builtin=True,
        ),
        InfographicTemplate(
            id=BUILTIN_TEMPLATE_IDS[InfographicType.FLOWCHART.value],
            name="flowchart",
            svg_template=_FLOWCHART_TEMPLATE,
            required_data_fields=["title", "nodes"],
            is_builtin=True,
        ),
        InfographicTemplate(
            id=BUILTIN_TEMPLATE_IDS[InfographicType.COMPARISON.value],
            name="comparison",
            svg_template=_COMPARISON_TEMPLATE,
            required_data_fields=[
                "title",
                "left_label",
                "right_label",
                "left_items",
                "right_items",
            ],
            is_builtin=True,
        ),
    ]


BUILTIN_TEMPLATES: list[InfographicTemplate] = _make_builtin_templates()
BUILTIN_TEMPLATES_BY_ID: dict[uuid.UUID, InfographicTemplate] = {t.id: t for t in BUILTIN_TEMPLATES}
BUILTIN_TEMPLATES_BY_NAME: dict[str, InfographicTemplate] = {t.name: t for t in BUILTIN_TEMPLATES}

# ---------------------------------------------------------------------------
# Colour palette helpers
# ---------------------------------------------------------------------------

_PALETTE = [
    "#4e79a7",
    "#f28e2b",
    "#e15759",
    "#76b7b2",
    "#59a14f",
    "#edc948",
    "#b07aa1",
    "#ff9da7",
    "#9c755f",
    "#bab0ac",
]


def _color(index: int) -> str:
    return _PALETTE[index % len(_PALETTE)]


# ---------------------------------------------------------------------------
# SVG Infographic Service
# ---------------------------------------------------------------------------


class SVGInfographicService:
    """Generate SVG infographics from data."""

    # ------------------------------------------------------------------
    # Pie chart
    # ------------------------------------------------------------------

    def create_pie_chart(self, data: dict[str, Any]) -> str:
        """Generate a pie-chart SVG.

        Expected data keys:
          - title: str
          - slices: list[{"label": str, "value": float}]
          - width: int  (optional, default 400)
          - height: int (optional, default 400)
        """
        title = data.get("title", "Pie Chart")
        slices = data.get("slices", [])
        width = int(data.get("width", 400))
        height = int(data.get("height", 400))

        cx = width / 2
        cy = height / 2
        radius = min(cx, cy) * 0.65

        total = sum(float(s["value"]) for s in slices) or 1.0

        svg_slices: list[str] = []
        legend_items: list[str] = []
        angle = -math.pi / 2  # start at top

        for i, s in enumerate(slices):
            value = float(s["value"])
            label = s.get("label", f"Item {i + 1}")
            sweep = 2 * math.pi * value / total
            end_angle = angle + sweep

            # SVG arc
            x1 = cx + radius * math.cos(angle)
            y1 = cy + radius * math.sin(angle)
            x2 = cx + radius * math.cos(end_angle)
            y2 = cy + radius * math.sin(end_angle)
            large_arc = 1 if sweep > math.pi else 0
            color = _color(i)

            path = (
                f'<path d="M {cx:.2f} {cy:.2f} '
                f"L {x1:.2f} {y1:.2f} "
                f"A {radius:.2f} {radius:.2f} 0 {large_arc} 1 {x2:.2f} {y2:.2f} "
                f'Z" fill="{color}" stroke="white" stroke-width="1.5"/>'
            )
            svg_slices.append(path)

            # Legend
            ly = height - 20 - (len(slices) - i - 1) * 20
            legend_items.append(
                f'<rect x="{width - 120}" y="{ly - 12}" width="14" height="14" fill="{color}"/>'
                f'<text x="{width - 102}" y="{ly}" font-size="11" fill="#333">{label}: {value:.0f}</text>'
            )
            angle = end_angle

        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">\n'
            f"  <title>{title}</title>\n"
            + "\n".join(f"  {s}" for s in svg_slices)
            + "\n"
            + f'  <text x="{cx:.2f}" y="{cy - radius - 10:.2f}" text-anchor="middle" '
            f'font-size="14" fill="#333" font-weight="bold">{title}</text>\n'
            + "\n".join(f"  {item}" for item in legend_items)
            + "\n</svg>"
        )

    # ------------------------------------------------------------------
    # Bar chart
    # ------------------------------------------------------------------

    def create_bar_chart(self, data: dict[str, Any]) -> str:
        """Generate a bar-chart SVG.

        Expected data keys:
          - title: str
          - bars: list[{"label": str, "value": float}]
          - width: int  (optional, default 500)
          - height: int (optional, default 350)
        """
        title = data.get("title", "Bar Chart")
        bars = data.get("bars", [])
        width = int(data.get("width", 500))
        height = int(data.get("height", 350))

        margin_left = 50
        margin_right = 20
        margin_top = 50
        margin_bottom = 60

        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        max_val = max((float(b["value"]) for b in bars), default=1.0) or 1.0

        n = len(bars) or 1
        bar_width = chart_width / n * 0.7
        gap = chart_width / n * 0.3

        svg_bars: list[str] = []
        x_pos = margin_left + gap / 2

        for i, b in enumerate(bars):
            value = float(b["value"])
            label = b.get("label", f"Item {i + 1}")
            bar_h = chart_height * value / max_val
            bar_y = margin_top + chart_height - bar_h
            color = _color(i)

            svg_bars.append(
                f'<rect x="{x_pos:.2f}" y="{bar_y:.2f}" '
                f'width="{bar_width:.2f}" height="{bar_h:.2f}" fill="{color}"/>'
            )
            label_x = x_pos + bar_width / 2
            svg_bars.append(
                f'<text x="{label_x:.2f}" y="{margin_top + chart_height + 18}" '
                f'text-anchor="middle" font-size="11" fill="#333">{label}</text>'
            )
            svg_bars.append(
                f'<text x="{label_x:.2f}" y="{bar_y - 4:.2f}" '
                f'text-anchor="middle" font-size="10" fill="#555">{value:.0f}</text>'
            )
            x_pos += bar_width + gap

        # Axis
        axis_bottom = margin_top + chart_height
        axis_right = margin_left + chart_width

        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">\n'
            f"  <title>{title}</title>\n"
            f'  <line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{axis_bottom}" '
            f'stroke="#888" stroke-width="1.5"/>\n'
            f'  <line x1="{margin_left}" y1="{axis_bottom}" x2="{axis_right}" y2="{axis_bottom}" '
            f'stroke="#888" stroke-width="1.5"/>\n'
            + "\n".join(f"  {b}" for b in svg_bars)
            + "\n"
            + f'  <text x="{width / 2:.2f}" y="26" text-anchor="middle" '
            f'font-size="16" fill="#333" font-weight="bold">{title}</text>\n' + "</svg>"
        )

    # ------------------------------------------------------------------
    # Template-based rendering
    # ------------------------------------------------------------------

    def create_from_template(self, template: InfographicTemplate, data: dict[str, Any]) -> str:
        """Fill an SVG template with data, delegating to typed generators where available."""
        if template.name == InfographicType.PIE_CHART.value:
            return self.create_pie_chart(data)
        if template.name == InfographicType.BAR_CHART.value:
            return self.create_bar_chart(data)
        if template.name == InfographicType.TIMELINE.value:
            return self._create_timeline(data)
        if template.name == InfographicType.FLOWCHART.value:
            return self._create_flowchart(data)
        if template.name == InfographicType.COMPARISON.value:
            return self._create_comparison(data)
        # Fallback: simple Python str.format_map substitution
        return template.svg_template.format_map(data)

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------

    def _create_timeline(self, data: dict[str, Any]) -> str:
        title = data.get("title", "Timeline")
        events = data.get("events", [])
        width = int(data.get("width", 600))
        height = int(data.get("height", max(200, 80 + len(events) * 60)))

        axis_x = 100
        start_y = 60
        step = (height - start_y - 30) / max(len(events), 1)

        svg_events: list[str] = []
        for i, ev in enumerate(events):
            label = ev.get("label", f"Event {i + 1}")
            date_str = ev.get("date", "")
            ey = start_y + i * step + step / 2
            color = _color(i)
            svg_events.append(
                f'<circle cx="{axis_x}" cy="{ey:.2f}" r="8" fill="{color}" stroke="white" stroke-width="1.5"/>'
            )
            svg_events.append(
                f'<text x="{axis_x + 16}" y="{ey + 5:.2f}" font-size="13" fill="#333" font-weight="bold">{label}</text>'
            )
            if date_str:
                svg_events.append(
                    f'<text x="{axis_x - 10}" y="{ey - 14:.2f}" font-size="10" fill="#888" text-anchor="end">{date_str}</text>'
                )

        end_y = start_y + len(events) * step if events else height - 30

        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">\n'
            f"  <title>{title}</title>\n"
            f'  <line x1="{axis_x}" y1="{start_y - 10}" x2="{axis_x}" y2="{end_y:.2f}" '
            f'stroke="#aaa" stroke-width="3"/>\n'
            + "\n".join(f"  {e}" for e in svg_events)
            + "\n"
            + f'  <text x="{width / 2:.2f}" y="26" text-anchor="middle" '
            f'font-size="16" fill="#333" font-weight="bold">{title}</text>\n' + "</svg>"
        )

    # ------------------------------------------------------------------
    # Flowchart
    # ------------------------------------------------------------------

    def _create_flowchart(self, data: dict[str, Any]) -> str:
        title = data.get("title", "Flowchart")
        nodes = data.get("nodes", [])
        width = int(data.get("width", 400))
        height = int(data.get("height", max(200, 80 + len(nodes) * 80)))

        box_w = 200
        box_h = 40
        cx = width / 2
        start_y = 60

        svg_nodes: list[str] = []
        svg_arrows: list[str] = []

        prev_by: float | None = None
        for i, node in enumerate(nodes):
            label = node.get("label", f"Step {i + 1}")
            bx = cx - box_w / 2
            by = start_y + i * 80
            color = _color(i)

            svg_nodes.append(
                f'<rect x="{bx:.2f}" y="{by:.2f}" width="{box_w}" height="{box_h}" '
                f'rx="6" ry="6" fill="{color}" opacity="0.85"/>'
            )
            svg_nodes.append(
                f'<text x="{cx:.2f}" y="{by + box_h / 2 + 5:.2f}" text-anchor="middle" '
                f'font-size="13" fill="white">{label}</text>'
            )

            if prev_by is not None:
                arrow_start = prev_by + box_h
                arrow_end = by
                svg_arrows.append(
                    f'<line x1="{cx:.2f}" y1="{arrow_start:.2f}" x2="{cx:.2f}" y2="{arrow_end:.2f}" '
                    f'stroke="#888" stroke-width="2" marker-end="url(#arrowhead)"/>'
                )
            prev_by = by

        defs = (
            '<defs><marker id="arrowhead" markerWidth="10" markerHeight="7" '
            'refX="10" refY="3.5" orient="auto">'
            '<polygon points="0 0, 10 3.5, 0 7" fill="#888"/>'
            "</marker></defs>"
        )

        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">\n'
            f"  <title>{title}</title>\n"
            f"  {defs}\n"
            + "\n".join(f"  {a}" for a in svg_arrows)
            + "\n"
            + "\n".join(f"  {n}" for n in svg_nodes)
            + "\n"
            + f'  <text x="{cx:.2f}" y="26" text-anchor="middle" '
            f'font-size="16" fill="#333" font-weight="bold">{title}</text>\n' + "</svg>"
        )

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def _create_comparison(self, data: dict[str, Any]) -> str:
        title = data.get("title", "Comparison")
        left_label = data.get("left_label", "Option A")
        right_label = data.get("right_label", "Option B")
        left_items: list[str] = data.get("left_items", [])
        right_items: list[str] = data.get("right_items", [])
        width = int(data.get("width", 600))
        n_rows = max(len(left_items), len(right_items), 1)
        height = int(data.get("height", 80 + n_rows * 36))

        half = width / 2
        header_y = 55

        def _items_svg(items: list[str], start_x: float, col_width: float) -> str:
            parts = []
            for j, item in enumerate(items):
                y = header_y + 30 + j * 34
                parts.append(
                    f'<text x="{start_x + col_width / 2:.2f}" y="{y}" '
                    f'text-anchor="middle" font-size="12" fill="#333">{item}</text>'
                )
            return "\n".join(parts)

        left_svg = _items_svg(left_items, 0, half)
        right_svg = _items_svg(right_items, half, half)

        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">\n'
            f"  <title>{title}</title>\n"
            f'  <rect x="0" y="0" width="{half:.2f}" height="{height}" fill="#e8f4f8"/>\n'
            f'  <rect x="{half:.2f}" y="0" width="{half:.2f}" height="{height}" fill="#fef9e7"/>\n'
            f'  <line x1="{half:.2f}" y1="0" x2="{half:.2f}" y2="{height}" '
            f'stroke="#ccc" stroke-width="2"/>\n'
            f'  <text x="{half / 2:.2f}" y="{header_y}" text-anchor="middle" '
            f'font-size="16" fill="#2c7bb6" font-weight="bold">{left_label}</text>\n'
            f'  <text x="{half + half / 2:.2f}" y="{header_y}" text-anchor="middle" '
            f'font-size="16" fill="#d7191c" font-weight="bold">{right_label}</text>\n'
            + f"  {left_svg}\n"
            + f"  {right_svg}\n"
            + f'  <text x="{width / 2:.2f}" y="26" text-anchor="middle" '
            f'font-size="16" fill="#333" font-weight="bold">{title}</text>\n' + "</svg>"
        )
