"""Media domain value objects and enumerations."""

from __future__ import annotations

from enum import Enum


class AssetType(Enum):
    IMAGE = "image"
    INFOGRAPHIC = "infographic"
    ICON = "icon"


class InfographicType(Enum):
    PIE_CHART = "pie_chart"
    BAR_CHART = "bar_chart"
    TIMELINE = "timeline"
    FLOWCHART = "flowchart"
    COMPARISON = "comparison"
