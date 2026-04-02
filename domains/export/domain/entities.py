"""Export domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from shared.domain.entity import AggregateRoot

from .value_objects import ExportFormat, ExportStatus


@dataclass(eq=False)
class ExportJob(AggregateRoot):
    """Aggregate root representing a single export task."""

    presentation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    format: ExportFormat = ExportFormat.PDF
    status: ExportStatus = ExportStatus.PENDING
    output_path: str | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def mark_processing(self) -> None:
        self.status = ExportStatus.PROCESSING

    def mark_completed(self, output_path: str) -> None:
        self.status = ExportStatus.COMPLETED
        self.output_path = output_path
        self.completed_at = datetime.now(UTC)

    def mark_failed(self, error_message: str) -> None:
        self.status = ExportStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now(UTC)
