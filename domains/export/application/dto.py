"""Export application-layer DTOs."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExportJobDTO:
    id: str
    presentation_id: str
    format: str
    status: str
    output_path: str | None
    error_message: str | None
    created_at: str
    completed_at: str | None

    @classmethod
    def from_entity(cls, job: object) -> ExportJobDTO:  # typed loosely to avoid circular imports
        from domains.export.domain.entities import ExportJob

        assert isinstance(job, ExportJob)
        return cls(
            id=str(job.id),
            presentation_id=str(job.presentation_id),
            format=job.format.value,
            status=job.status.value,
            output_path=job.output_path,
            error_message=job.error_message,
            created_at=job.created_at.isoformat(),
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
        )
