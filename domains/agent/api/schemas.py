"""Agent API Pydantic schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RunPipelineRequest(BaseModel):
    topic: str
    presentation_id: str
    pipeline_name: str = "default"
    config: dict | None = None


class ConfigureAgentRequest(BaseModel):
    model: str | None = None
    provider: str | None = None
    system_prompt: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    tools: list[str] | None = None


class StartRalphLoopRequest(BaseModel):
    config: dict | None = None


class ApproveRalphLoopRequest(BaseModel):
    approved: bool
    feedback: str | None = None


class AgentConfigResponse(BaseModel):
    model: str
    provider: str
    system_prompt: str
    temperature: float
    max_tokens: int
    tools: list[str]


class AgentResponse(BaseModel):
    id: str
    name: str
    config: AgentConfigResponse
    enabled: bool


class SubAgentRunResponse(BaseModel):
    id: str
    agent_name: str
    status: str
    result: dict | None = None
    error: str | None = None
    started_at: str = ""
    completed_at: str | None = None


class AgentRunResponse(BaseModel):
    id: str
    pipeline_id: str
    presentation_id: str
    status: str
    current_stage: str
    sub_agent_runs: list[SubAgentRunResponse] = []
    started_at: str = ""
    completed_at: str | None = None


class ChecklistItemResponse(BaseModel):
    criterion: str
    weight: float
    passed: bool
    details: str


class RalphIterationResponse(BaseModel):
    iteration_number: int
    checklist_results: list[ChecklistItemResponse]
    weighted_score: float
    action_taken: str


class RalphLoopResponse(BaseModel):
    id: str
    agent_run_id: str
    status: str
    iterations: list[RalphIterationResponse] = []
    current_score: float = 0.0
