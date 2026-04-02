"""Rendering domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from shared.domain.entity import AggregateRoot, Entity

from .value_objects import RenderConfig, RenderStatus


@dataclass
class RenderedSlide(Entity):
    """A single rendered slide with its HTML output."""

    slide_id: uuid.UUID = field(default_factory=uuid.uuid4)
    html: str = ""
    thumbnail_url: str | None = None
    render_time_ms: int = 0


@dataclass
class RenderJob(AggregateRoot):
    """Aggregate root tracking an entire presentation render job."""

    presentation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    rendered_slides: list[RenderedSlide] = field(default_factory=list)
    config: RenderConfig = field(default_factory=RenderConfig)
    status: RenderStatus = RenderStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def start_rendering(self) -> None:
        if self.status != RenderStatus.PENDING:
            raise ValueError(f"Cannot start rendering from status '{self.status.value}'")
        self.status = RenderStatus.RENDERING

    def add_rendered_slide(self, rendered_slide: RenderedSlide) -> None:
        self.rendered_slides.append(rendered_slide)

    def complete(self) -> None:
        if self.status != RenderStatus.RENDERING:
            raise ValueError(f"Cannot complete from status '{self.status.value}'")
        self.status = RenderStatus.COMPLETED
        self.completed_at = datetime.now(UTC)

    def fail(self) -> None:
        self.status = RenderStatus.FAILED
        self.completed_at = datetime.now(UTC)

    def get_rendered_slide(self, slide_id: uuid.UUID) -> RenderedSlide | None:
        return next((s for s in self.rendered_slides if s.slide_id == slide_id), None)
