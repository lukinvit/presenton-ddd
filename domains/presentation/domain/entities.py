"""Presentation domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from shared.domain.entity import AggregateRoot, Entity

from .value_objects import PresentationStatus, SlideElement


@dataclass
class Slide(Entity):
    """An ordered slide within a presentation."""

    presentation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    index: int = 0
    title: str = ""
    elements: list[SlideElement] = field(default_factory=list)
    speaker_notes: str = ""
    layout_type: str = "content"

    def add_element(self, element: SlideElement) -> None:
        self.elements.append(element)

    def replace_elements(self, elements: list[SlideElement]) -> None:
        self.elements = list(elements)


@dataclass
class Template(Entity):
    """A reusable HTML/CSS presentation template."""

    name: str = ""
    description: str = ""
    html_template: str = ""
    css: str = ""
    is_builtin: bool = False


@dataclass
class Presentation(AggregateRoot):
    """Aggregate root for the presentation bounded context."""

    title: str = ""
    description: str = ""
    slides: list[Slide] = field(default_factory=list)
    template_id: uuid.UUID | None = None
    style_profile_id: uuid.UUID | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: PresentationStatus = PresentationStatus.DRAFT

    # ------------------------------------------------------------------
    # Slide management helpers
    # ------------------------------------------------------------------

    def add_slide(self, slide: Slide) -> None:
        """Append a slide and keep index consistent."""
        slide.index = len(self.slides)
        self.slides.append(slide)
        self.updated_at = datetime.now(UTC)

    def insert_slide(self, slide: Slide, index: int) -> None:
        """Insert a slide at the given position, re-indexing subsequent slides."""
        self.slides.insert(index, slide)
        self._reindex()
        self.updated_at = datetime.now(UTC)

    def remove_slide(self, slide_id: uuid.UUID) -> None:
        self.slides = [s for s in self.slides if s.id != slide_id]
        self._reindex()
        self.updated_at = datetime.now(UTC)

    def get_slide(self, slide_id: uuid.UUID) -> Slide | None:
        return next((s for s in self.slides if s.id == slide_id), None)

    def reorder_slides(self, slide_ids: list[uuid.UUID]) -> None:
        """Reorder slides according to the provided id sequence."""
        by_id = {s.id: s for s in self.slides}
        self.slides = [by_id[sid] for sid in slide_ids if sid in by_id]
        self._reindex()
        self.updated_at = datetime.now(UTC)

    def update_title(self, title: str) -> None:
        self.title = title
        self.updated_at = datetime.now(UTC)

    def update_description(self, description: str) -> None:
        self.description = description
        self.updated_at = datetime.now(UTC)

    def update_status(self, status: PresentationStatus) -> None:
        self.status = status
        self.updated_at = datetime.now(UTC)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _reindex(self) -> None:
        for i, slide in enumerate(self.slides):
            slide.index = i
