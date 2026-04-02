"""Tests for the agent MCP server tool registration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest

from domains.agent.domain.entities import Agent, AgentPipeline, AgentRun, RalphLoop
from domains.agent.domain.services import SubAgentExecutor, SubAgentResult, SubAgentTask
from domains.agent.domain.value_objects import RunStatus
from domains.agent.mcp.server import create_agent_mcp_server
from shared.domain.events import DomainEvent

# ---------- In-memory repos (reused pattern) ----------


@dataclass
class InMemoryAgentRunRepo:
    _store: dict[uuid.UUID, AgentRun] = field(default_factory=dict)

    async def get(self, id: uuid.UUID) -> AgentRun | None:
        return self._store.get(id)

    async def save(self, run: AgentRun) -> None:
        self._store[run.id] = run


@dataclass
class InMemoryAgentPipelineRepo:
    _store: dict[uuid.UUID, AgentPipeline] = field(default_factory=dict)
    _by_name: dict[str, AgentPipeline] = field(default_factory=dict)

    async def get(self, id: uuid.UUID) -> AgentPipeline | None:
        return self._store.get(id)

    async def get_by_name(self, name: str) -> AgentPipeline | None:
        return self._by_name.get(name)

    async def save(self, pipeline: AgentPipeline) -> None:
        self._store[pipeline.id] = pipeline
        self._by_name[pipeline.name] = pipeline


@dataclass
class InMemoryAgentRepo:
    _store: dict[uuid.UUID, Agent] = field(default_factory=dict)
    _by_name: dict[str, Agent] = field(default_factory=dict)

    async def get(self, id: uuid.UUID) -> Agent | None:
        return self._store.get(id)

    async def get_by_name(self, name: str) -> Agent | None:
        return self._by_name.get(name)

    async def list_all(self) -> list[Agent]:
        return list(self._store.values())

    async def save(self, agent: Agent) -> None:
        self._store[agent.id] = agent
        self._by_name[agent.name] = agent


@dataclass
class InMemoryRalphLoopRepo:
    _store: dict[uuid.UUID, RalphLoop] = field(default_factory=dict)
    _by_run: dict[uuid.UUID, RalphLoop] = field(default_factory=dict)

    async def get(self, id: uuid.UUID) -> RalphLoop | None:
        return self._store.get(id)

    async def get_by_run_id(self, agent_run_id: uuid.UUID) -> RalphLoop | None:
        return self._by_run.get(agent_run_id)

    async def save(self, loop: RalphLoop) -> None:
        self._store[loop.id] = loop
        self._by_run[loop.agent_run_id] = loop


@dataclass
class InMemoryEventBus:
    events: list[DomainEvent] = field(default_factory=list)

    async def publish(self, event: DomainEvent) -> None:
        self.events.append(event)

    async def subscribe(self, event_type: str, handler: Any) -> None:
        pass


class SuccessRunner:
    async def invoke(self, task: SubAgentTask) -> SubAgentResult:
        return SubAgentResult(agent_name=task.agent_name, success=True, result={"ok": True})


# ---------- Tests ----------


class TestAgentMCPServer:
    def _make_server(self):
        return create_agent_mcp_server(
            run_repo=InMemoryAgentRunRepo(),
            pipeline_repo=InMemoryAgentPipelineRepo(),
            agent_repo=InMemoryAgentRepo(),
            ralph_repo=InMemoryRalphLoopRepo(),
            executor=SubAgentExecutor(runner=SuccessRunner(), max_concurrent=4),
            event_bus=InMemoryEventBus(),
        )

    def test_all_tools_registered(self) -> None:
        server = self._make_server()
        expected_tools = {
            "agent.run_pipeline",
            "agent.configure",
            "agent.list_agents",
            "agent.update_agent",
            "agent.ralph_loop.start",
            "agent.ralph_loop.status",
            "agent.ralph_loop.approve",
            "health.check",
        }
        assert set(server.registered_tools.keys()) == expected_tools

    @pytest.mark.asyncio
    async def test_list_agents_tool(self) -> None:
        server = self._make_server()
        result = await server.registered_tools["agent.list_agents"]()
        assert "agents" in result
        assert len(result["agents"]) == 13  # defaults

    @pytest.mark.asyncio
    async def test_configure_tool(self) -> None:
        server = self._make_server()
        result = await server.registered_tools["agent.configure"](
            agent_name="ContentWriter", model="gpt-4o"
        )
        assert result["name"] == "ContentWriter"
        assert result["config"]["model"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_run_pipeline_tool(self) -> None:
        server = self._make_server()
        result = await server.registered_tools["agent.run_pipeline"](
            topic="Test topic",
            presentation_id=str(uuid.uuid4()),
        )
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_ralph_loop_lifecycle(self) -> None:
        """Start a ralph loop, check status, then approve."""
        run_repo = InMemoryAgentRunRepo()
        ralph_repo = InMemoryRalphLoopRepo()
        event_bus = InMemoryEventBus()

        run = AgentRun(id=uuid.uuid4(), status=RunStatus.RUNNING)
        await run_repo.save(run)

        server = create_agent_mcp_server(
            run_repo=run_repo,
            pipeline_repo=InMemoryAgentPipelineRepo(),
            agent_repo=InMemoryAgentRepo(),
            ralph_repo=ralph_repo,
            executor=SubAgentExecutor(runner=SuccessRunner(), max_concurrent=4),
            event_bus=event_bus,
        )

        # Start
        start_result = await server.registered_tools["agent.ralph_loop.start"](
            agent_run_id=str(run.id)
        )
        loop_id = start_result["id"]
        assert start_result["status"] == "running"

        # Status
        status_result = await server.registered_tools["agent.ralph_loop.status"](
            ralph_loop_id=loop_id
        )
        assert status_result["status"] == "running"

        # Approve
        approve_result = await server.registered_tools["agent.ralph_loop.approve"](
            ralph_loop_id=loop_id, approved=True
        )
        assert approve_result["status"] == "approved"
