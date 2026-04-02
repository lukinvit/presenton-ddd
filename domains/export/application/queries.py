"""Export application queries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from domains.export.application.dto import ExportJobDTO
from domains.export.domain.repositories import ExportJobRepository


@dataclass
class GetExportJobQuery:
    job_repo: ExportJobRepository

    async def execute(self, job_id: uuid.UUID) -> ExportJobDTO:
        job = await self.job_repo.get(job_id)
        if job is None:
            raise ValueError(f"Export job '{job_id}' not found")
        return ExportJobDTO.from_entity(job)


@dataclass
class ListExportJobsQuery:
    job_repo: ExportJobRepository

    async def execute(self, presentation_id: uuid.UUID) -> list[ExportJobDTO]:
        jobs = await self.job_repo.list_by_presentation(presentation_id)
        return [ExportJobDTO.from_entity(j) for j in jobs]
