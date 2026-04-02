"""Agent application DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentConfigDTO:
    model: str
    provider: str
    system_prompt: str
    temperature: float
    max_tokens: int
    tools: list[str]


@dataclass
class AgentDTO:
    id: str
    name: str
    config: AgentConfigDTO
    enabled: bool


@dataclass
class SubAgentRunDTO:
    id: str
    agent_name: str
    status: str
    result: dict | None = None
    error: str | None = None
    started_at: str = ""
    completed_at: str | None = None


@dataclass
class AgentRunDTO:
    id: str
    pipeline_id: str
    presentation_id: str
    status: str
    current_stage: str
    sub_agent_runs: list[SubAgentRunDTO] = field(default_factory=list)
    started_at: str = ""
    completed_at: str | None = None


@dataclass
class ChecklistItemDTO:
    criterion: str
    weight: float
    passed: bool
    details: str


@dataclass
class RalphIterationDTO:
    iteration_number: int
    checklist_results: list[ChecklistItemDTO]
    weighted_score: float
    action_taken: str


@dataclass
class RalphLoopDTO:
    id: str
    agent_run_id: str
    status: str
    iterations: list[RalphIterationDTO] = field(default_factory=list)
    current_score: float = 0.0
