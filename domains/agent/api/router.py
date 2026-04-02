"""Agent API router."""

from __future__ import annotations

import uuid
from dataclasses import asdict

from fastapi import APIRouter, HTTPException

from domains.agent.api.schemas import (
    AgentResponse,
    AgentRunResponse,
    ApproveRalphLoopRequest,
    ConfigureAgentRequest,
    RalphLoopResponse,
    RunPipelineRequest,
    StartRalphLoopRequest,
)
from domains.agent.application.commands import (
    ApproveRalphLoopCommand,
    ConfigureAgentCommand,
    RunPipelineCommand,
    StartRalphLoopCommand,
)
from domains.agent.application.queries import (
    GetAgentRunQuery,
    GetRalphLoopStatusQuery,
    ListAgentsQuery,
)
from domains.agent.domain.repositories import (
    AgentPipelineRepository,
    AgentRepository,
    AgentRunRepository,
    RalphLoopRepository,
)
from domains.agent.domain.services import SubAgentExecutor
from shared.domain.events import EventBus


def create_agent_router(
    run_repo: AgentRunRepository,
    pipeline_repo: AgentPipelineRepository,
    agent_repo: AgentRepository,
    ralph_repo: RalphLoopRepository,
    executor: SubAgentExecutor,
    event_bus: EventBus,
) -> APIRouter:
    router = APIRouter(tags=["agents"])

    @router.post("/agents/pipeline", response_model=AgentRunResponse, status_code=202)
    async def run_pipeline(req: RunPipelineRequest) -> AgentRunResponse:
        cmd = RunPipelineCommand(
            run_repo=run_repo,
            pipeline_repo=pipeline_repo,
            agent_repo=agent_repo,
            executor=executor,
            event_bus=event_bus,
        )
        try:
            result = await cmd.execute(
                topic=req.topic,
                presentation_id=uuid.UUID(req.presentation_id),
                pipeline_name=req.pipeline_name,
                config=req.config,
            )
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e
        return AgentRunResponse(**asdict(result))

    @router.get("/agents/runs/{run_id}", response_model=AgentRunResponse)
    async def get_agent_run(run_id: str) -> AgentRunResponse:
        query = GetAgentRunQuery(run_repo=run_repo)
        try:
            result = await query.execute(uuid.UUID(run_id))
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return AgentRunResponse(**asdict(result))

    @router.get("/agents", response_model=list[AgentResponse])
    async def list_agents() -> list[AgentResponse]:
        query = ListAgentsQuery(agent_repo=agent_repo)
        results = await query.execute()
        return [AgentResponse(**asdict(r)) for r in results]

    @router.put("/agents/{agent_name}", response_model=AgentResponse)
    async def configure_agent(agent_name: str, req: ConfigureAgentRequest) -> AgentResponse:
        cmd = ConfigureAgentCommand(agent_repo=agent_repo)
        result = await cmd.execute(
            agent_name=agent_name,
            model=req.model,
            provider=req.provider,
            system_prompt=req.system_prompt,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            tools=req.tools,
        )
        return AgentResponse(**asdict(result))

    @router.post(
        "/agents/ralph-loop/{run_id}/start",
        response_model=RalphLoopResponse,
        status_code=201,
    )
    async def start_ralph_loop(run_id: str, req: StartRalphLoopRequest) -> RalphLoopResponse:
        cmd = StartRalphLoopCommand(
            ralph_repo=ralph_repo,
            run_repo=run_repo,
            event_bus=event_bus,
        )
        try:
            result = await cmd.execute(agent_run_id=uuid.UUID(run_id), config=req.config)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return RalphLoopResponse(**asdict(result))

    @router.post(
        "/agents/ralph-loop/{loop_id}/approve",
        response_model=RalphLoopResponse,
    )
    async def approve_ralph_loop(loop_id: str, req: ApproveRalphLoopRequest) -> RalphLoopResponse:
        cmd = ApproveRalphLoopCommand(
            ralph_repo=ralph_repo,
            run_repo=run_repo,
            event_bus=event_bus,
        )
        try:
            result = await cmd.execute(
                ralph_loop_id=uuid.UUID(loop_id),
                approved=req.approved,
                feedback=req.feedback,
            )
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return RalphLoopResponse(**asdict(result))

    @router.get(
        "/agents/ralph-loop/{loop_id}",
        response_model=RalphLoopResponse,
    )
    async def get_ralph_loop(loop_id: str) -> RalphLoopResponse:
        query = GetRalphLoopStatusQuery(ralph_repo=ralph_repo)
        try:
            result = await query.execute(uuid.UUID(loop_id))
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return RalphLoopResponse(**asdict(result))

    return router
