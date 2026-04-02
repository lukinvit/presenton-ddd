"""Export domain repository protocols."""

from __future__ import annotations

import uuid
from typing import Protocol

from .entities import ExportJob


class ExportJobRepository(Protocol):
    async def get(self, job_id: uuid.UUID) -> ExportJob | None: ...
    async def save(self, job: ExportJob) -> None: ...
    async def list_by_presentation(self, presentation_id: uuid.UUID) -> list[ExportJob]: ...
