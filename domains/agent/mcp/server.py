"""Agent domain MCP server."""

from __future__ import annotations

import uuid
from dataclasses import asdict

from domains.agent.application.commands import (
    ApproveRalphLoopCommand,
    ConfigureAgentCommand,
    RunPipelineCommand,
    StartRalphLoopCommand,
)
from domains.agent.application.queries import (
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
from shared.mcp.server_base import DomainMCPServer


def create_agent_mcp_server(
    run_repo: AgentRunRepository,
    pipeline_repo: AgentPipelineRepository,
    agent_repo: AgentRepository,
    ralph_repo: RalphLoopRepository,
    executor: SubAgentExecutor,
    event_bus: EventBus,
) -> DomainMCPServer:
    server = DomainMCPServer(name="agent", port=9086)

    @server.tool("agent.run_pipeline")
    async def run_pipeline(
        topic: str,
        presentation_id: str,
        pipeline_name: str = "default",
    ) -> dict:
        cmd = RunPipelineCommand(
            run_repo=run_repo,
            pipeline_repo=pipeline_repo,
            agent_repo=agent_repo,
            executor=executor,
            event_bus=event_bus,
        )
        result = await cmd.execute(
            topic=topic,
            presentation_id=uuid.UUID(presentation_id),
            pipeline_name=pipeline_name,
        )
        return asdict(result)

    @server.tool("agent.configure")
    async def configure_agent(
        agent_name: str,
        model: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict:
        cmd = ConfigureAgentCommand(agent_repo=agent_repo)
        result = await cmd.execute(
            agent_name=agent_name,
            model=model,
            provider=provider,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return asdict(result)

    @server.tool("agent.list_agents")
    async def list_agents() -> dict:
        query = ListAgentsQuery(agent_repo=agent_repo)
        results = await query.execute()
        return {"agents": [asdict(a) for a in results]}

    @server.tool("agent.update_agent")
    async def update_agent(
        agent_name: str,
        model: str | None = None,
        provider: str | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[str] | None = None,
    ) -> dict:
        cmd = ConfigureAgentCommand(agent_repo=agent_repo)
        result = await cmd.execute(
            agent_name=agent_name,
            model=model,
            provider=provider,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
        )
        return asdict(result)

    @server.tool("agent.ralph_loop.start")
    async def ralph_loop_start(agent_run_id: str) -> dict:
        cmd = StartRalphLoopCommand(
            ralph_repo=ralph_repo,
            run_repo=run_repo,
            event_bus=event_bus,
        )
        result = await cmd.execute(agent_run_id=uuid.UUID(agent_run_id))
        return asdict(result)

    @server.tool("agent.ralph_loop.status")
    async def ralph_loop_status(ralph_loop_id: str) -> dict:
        query = GetRalphLoopStatusQuery(ralph_repo=ralph_repo)
        result = await query.execute(uuid.UUID(ralph_loop_id))
        return asdict(result)

    @server.tool("agent.ralph_loop.approve")
    async def ralph_loop_approve(
        ralph_loop_id: str,
        approved: bool,
        feedback: str | None = None,
    ) -> dict:
        cmd = ApproveRalphLoopCommand(
            ralph_repo=ralph_repo,
            run_repo=run_repo,
            event_bus=event_bus,
        )
        result = await cmd.execute(
            ralph_loop_id=uuid.UUID(ralph_loop_id),
            approved=approved,
            feedback=feedback,
        )
        return asdict(result)

    return server
