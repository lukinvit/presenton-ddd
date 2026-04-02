"""Agent domain value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from shared.domain.value_object import ValueObject


class RunStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"


@dataclass(frozen=True)
class AgentConfig(ValueObject):
    model: str = ""
    provider: str = "anthropic"
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    tools: tuple[str, ...] = ()


@dataclass(frozen=True)
class PipelineConfig(ValueObject):
    parallel_subagents: bool = True
    max_concurrent: int = 8


@dataclass(frozen=True)
class PipelineStage(ValueObject):
    name: str = ""
    agents: tuple[str, ...] = ()
    parallel: bool = False


@dataclass(frozen=True)
class RalphLoopConfig(ValueObject):
    max_iterations: int = 5
    threshold: float = 0.95
    auto_fix_enabled: bool = True
    human_approval_required: bool = True
    checklist_weights: dict[str, float] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(
            (
                self.max_iterations,
                self.threshold,
                self.auto_fix_enabled,
                self.human_approval_required,
                tuple(sorted(self.checklist_weights.items())),
            )
        )


@dataclass(frozen=True)
class ChecklistItem(ValueObject):
    criterion: str = ""
    weight: float = 1.0
    passed: bool = False
    details: str = ""


@dataclass(frozen=True)
class RalphIteration(ValueObject):
    iteration_number: int = 0
    checklist_results: tuple[ChecklistItem, ...] = ()
    weighted_score: float = 0.0
    action_taken: str = ""  # "auto_fix", "human_approved", "human_feedback"
