"""Presentation application queries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from domains.presentation.application.commands import _presentation_to_dto
from domains.presentation.application.dto import PresentationDTO
from domains.presentation.domain.repositories import PresentationRepository


@dataclass
class GetPresentationQuery:
    repo: PresentationRepository

    async def execute(self, presentation_id: uuid.UUID) -> PresentationDTO:
        presentation = await self.repo.get(presentation_id)
        if presentation is None:
            raise ValueError(f"Presentation '{presentation_id}' not found")
        return _presentation_to_dto(presentation)


@dataclass
class ListPresentationsQuery:
    repo: PresentationRepository

    async def execute(self, limit: int = 50, offset: int = 0) -> list[PresentationDTO]:
        presentations = await self.repo.list_all(limit=limit, offset=offset)
        return [_presentation_to_dto(p) for p in presentations]
