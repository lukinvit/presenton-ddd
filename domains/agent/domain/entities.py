"""Agent domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from shared.domain.entity import AggregateRoot, Entity

from .value_objects import (
    AgentConfig,
    ChecklistItem,
    PipelineConfig,
    PipelineStage,
    RalphIteration,
    RalphLoopConfig,
    RunStatus,
)


@dataclass
class Agent(Entity):
    name: str = ""
    config: AgentConfig = field(default_factory=AgentConfig)
    enabled: bool = True


@dataclass
class SubAgentRun(Entity):
    agent_run_id: uuid.UUID = field(default_factory=uuid.uuid4)
    agent_name: str = ""
    status: RunStatus = RunStatus.PENDING
    result: dict | None = None
    error: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    def start(self) -> None:
        self.status = RunStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def complete(self, result: dict) -> None:
        self.status = RunStatus.COMPLETED
        self.result = result
        self.completed_at = datetime.now(UTC)

    def fail(self, error: str) -> None:
        self.status = RunStatus.FAILED
        self.error = error
        self.completed_at = datetime.now(UTC)


@dataclass
class RalphLoop(Entity):
    agent_run_id: uuid.UUID = field(default_factory=uuid.uuid4)
    config: RalphLoopConfig = field(default_factory=RalphLoopConfig)
    iterations: list[RalphIteration] = field(default_factory=list)
    status: str = "running"  # running, approved, max_iterations_reached

    def add_iteration(
        self,
        checklist_results: list[ChecklistItem],
        action_taken: str,
    ) -> RalphIteration:
        weights_sum = sum(c.weight for c in checklist_results) or 1.0
        weighted_score = sum(c.weight for c in checklist_results if c.passed) / weights_sum
        iteration = RalphIteration(
            iteration_number=len(self.iterations) + 1,
            checklist_results=tuple(checklist_results),
            weighted_score=weighted_score,
            action_taken=action_taken,
        )
        self.iterations.append(iteration)
        return iteration

    @property
    def current_score(self) -> float:
        if not self.iterations:
            return 0.0
        return self.iterations[-1].weighted_score

    @property
    def iteration_count(self) -> int:
        return len(self.iterations)

    def meets_threshold(self) -> bool:
        return self.current_score >= self.config.threshold

    def max_iterations_reached(self) -> bool:
        return self.iteration_count >= self.config.max_iterations

    def approve(self) -> None:
        self.status = "approved"

    def reject_with_feedback(self) -> None:
        self.status = "running"

    def mark_max_iterations(self) -> None:
        self.status = "max_iterations_reached"

    def failed_criteria(self) -> list[ChecklistItem]:
        if not self.iterations:
            return []
        return [c for c in self.iterations[-1].checklist_results if not c.passed]


@dataclass
class AgentRun(AggregateRoot):
    pipeline_id: uuid.UUID = field(default_factory=uuid.uuid4)
    presentation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    status: RunStatus = RunStatus.PENDING
    current_stage: str = ""
    sub_agent_runs: list[SubAgentRun] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    def start(self) -> None:
        self.status = RunStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def set_stage(self, stage: str) -> None:
        self.current_stage = stage

    def complete(self) -> None:
        self.status = RunStatus.COMPLETED
        self.completed_at = datetime.now(UTC)

    def fail(self) -> None:
        self.status = RunStatus.FAILED
        self.completed_at = datetime.now(UTC)

    def wait_approval(self) -> None:
        self.status = RunStatus.WAITING_APPROVAL

    def add_sub_agent_run(self, sub_run: SubAgentRun) -> None:
        self.sub_agent_runs.append(sub_run)


@dataclass
class AgentPipeline(AggregateRoot):
    name: str = ""
    stages: list[PipelineStage] = field(default_factory=list)
    config: PipelineConfig = field(default_factory=PipelineConfig)
