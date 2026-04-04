"""In-memory agent repository implementations."""

from __future__ import annotations

import uuid

from domains.agent.domain.entities import Agent
from domains.agent.domain.defaults import DEFAULT_AGENTS


class InMemoryAgentRepository:
    def __init__(self) -> None:
        self._agents: dict[uuid.UUID, Agent] = {}
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        for name, config in DEFAULT_AGENTS.items():
            agent = Agent(id=uuid.uuid4(), name=name, config=config, enabled=True)
            self._agents[agent.id] = agent

    async def get(self, id: uuid.UUID) -> Agent | None:
        return self._agents.get(id)

    async def get_by_name(self, name: str) -> Agent | None:
        for agent in self._agents.values():
            if agent.name == name:
                return agent
        return None

    async def list_all(self) -> list[Agent]:
        return list(self._agents.values())

    async def save(self, agent: Agent) -> None:
        self._agents[agent.id] = agent

    async def delete(self, id: uuid.UUID) -> None:
        self._agents.pop(id, None)
