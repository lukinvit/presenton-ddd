"""Agent application queries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from domains.agent.application.commands import (
    _agent_to_dto,
    _ralph_loop_to_dto,
    _run_to_dto,
)
from domains.agent.application.dto import AgentDTO, AgentRunDTO, RalphLoopDTO
from domains.agent.domain.defaults import DEFAULT_AGENTS
from domains.agent.domain.entities import Agent
from domains.agent.domain.repositories import (
    AgentRepository,
    AgentRunRepository,
    RalphLoopRepository,
)


@dataclass
class GetAgentRunQuery:
    run_repo: AgentRunRepository

    async def execute(self, run_id: uuid.UUID) -> AgentRunDTO:
        run = await self.run_repo.get(run_id)
        if run is None:
            raise ValueError(f"AgentRun '{run_id}' not found")
        return _run_to_dto(run)


@dataclass
class ListAgentsQuery:
    agent_repo: AgentRepository

    async def execute(self) -> list[AgentDTO]:
        agents = await self.agent_repo.list_all()
        if not agents:
            # Return default agents if none configured yet
            return [
                _agent_to_dto(Agent(id=uuid.uuid4(), name=name, config=cfg))
                for name, cfg in DEFAULT_AGENTS.items()
            ]
        return [_agent_to_dto(a) for a in agents]


@dataclass
class GetRalphLoopStatusQuery:
    ralph_repo: RalphLoopRepository

    async def execute(self, ralph_loop_id: uuid.UUID) -> RalphLoopDTO:
        loop = await self.ralph_repo.get(ralph_loop_id)
        if loop is None:
            raise ValueError(f"RalphLoop '{ralph_loop_id}' not found")
        return _ralph_loop_to_dto(loop)
