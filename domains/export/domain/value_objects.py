"""Export domain value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExportFormat(Enum):
    PDF = "pdf"
    PPTX = "pptx"


class ExportStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class ExportConfig:
    format: ExportFormat
    include_speaker_notes: bool = False
    quality: str = "high"  # high / medium / low
