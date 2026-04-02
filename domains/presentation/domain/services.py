"""Presentation domain service — pure business logic."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from .entities import Presentation, Slide
from .value_objects import ElementType, PresentationStatus, SlideElement


@dataclass
class PresentationService:
    """Stateless domain service containing business rules."""

    def create_presentation(self, title: str, description: str = "") -> Presentation:
        return Presentation(
            id=uuid.uuid4(),
            title=title,
            description=description,
            status=PresentationStatus.DRAFT,
        )

    def create_slide(
        self,
        presentation_id: uuid.UUID,
        title: str,
        layout_type: str = "content",
        speaker_notes: str = "",
    ) -> Slide:
        return Slide(
            id=uuid.uuid4(),
            presentation_id=presentation_id,
            title=title,
            layout_type=layout_type,
            speaker_notes=speaker_notes,
        )

    def create_element(
        self,
        element_type: ElementType,
        content: str,
        position: dict | None = None,
        style: dict | None = None,
    ) -> SlideElement:
        return SlideElement(
            type=element_type,
            content=content,
            position=position or {"x": 0, "y": 0, "width": 100, "height": 100},
            style=style or {},
        )

    def finalize_presentation(self, presentation: Presentation) -> None:
        """Transition presentation to FINAL status."""
        if presentation.status == PresentationStatus.GENERATING:
            raise ValueError("Cannot finalize a presentation that is still generating.")
        presentation.update_status(PresentationStatus.FINAL)

    def validate_slide_order(self, presentation: Presentation, slide_ids: list[uuid.UUID]) -> None:
        """Ensure the supplied slide_ids matches the set of slides in the presentation."""
        existing_ids = {s.id for s in presentation.slides}
        supplied_ids = set(slide_ids)
        if existing_ids != supplied_ids:
            raise ValueError(
                "slide_ids must contain exactly the slides that exist in the presentation."
            )
