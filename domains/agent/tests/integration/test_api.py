"""Integration tests for the agent API router."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from domains.agent.api.router import create_agent_router
from domains.agent.domain.entities import Agent, AgentPipeline, AgentRun, RalphLoop
from domains.agent.domain.services import SubAgentExecutor, SubAgentResult, SubAgentTask
from domains.agent.domain.value_objects import RunStatus
from shared.domain.events import DomainEvent

# ---------- In-memory repos ----------


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


@pytest.fixture
def repos():
    return {
        "run_repo": InMemoryAgentRunRepo(),
        "pipeline_repo": InMemoryAgentPipelineRepo(),
        "agent_repo": InMemoryAgentRepo(),
        "ralph_repo": InMemoryRalphLoopRepo(),
        "event_bus": InMemoryEventBus(),
    }


@pytest.fixture
def client(repos):
    app = FastAPI()
    executor = SubAgentExecutor(runner=SuccessRunner(), max_concurrent=4)
    router = create_agent_router(executor=executor, **repos)
    app.include_router(router)
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestAgentAPI:
    @pytest.mark.asyncio
    async def test_run_pipeline(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/agents/pipeline",
            json={
                "topic": "AI in Healthcare",
                "presentation_id": str(uuid.uuid4()),
            },
        )
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "completed"
        assert data["current_stage"] == "EXPORT"

    @pytest.mark.asyncio
    async def test_get_run_not_found(self, client: AsyncClient) -> None:
        resp = await client.get(f"/agents/runs/{uuid.uuid4()}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_run_after_pipeline(self, client: AsyncClient, repos) -> None:
        resp = await client.post(
            "/agents/pipeline",
            json={"topic": "Test", "presentation_id": str(uuid.uuid4())},
        )
        run_id = resp.json()["id"]
        resp2 = await client.get(f"/agents/runs/{run_id}")
        assert resp2.status_code == 200
        assert resp2.json()["id"] == run_id

    @pytest.mark.asyncio
    async def test_list_agents_defaults(self, client: AsyncClient) -> None:
        resp = await client.get("/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 13

    @pytest.mark.asyncio
    async def test_configure_agent(self, client: AsyncClient) -> None:
        resp = await client.put(
            "/agents/ContentWriter",
            json={"model": "gpt-4o", "temperature": 0.3},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "ContentWriter"
        assert data["config"]["model"] == "gpt-4o"
        assert data["config"]["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_ralph_loop_flow(self, client: AsyncClient, repos) -> None:
        # Create a run first
        run = AgentRun(id=uuid.uuid4(), status=RunStatus.RUNNING)
        await repos["run_repo"].save(run)

        # Start ralph loop
        resp = await client.post(
            f"/agents/ralph-loop/{run.id}/start",
            json={},
        )
        assert resp.status_code == 201
        loop_data = resp.json()
        loop_id = loop_data["id"]
        assert loop_data["status"] == "running"

        # Get status
        resp = await client.get(f"/agents/ralph-loop/{loop_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

        # Approve
        resp = await client.post(
            f"/agents/ralph-loop/{loop_id}/approve",
            json={"approved": True, "feedback": "Looks great"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    @pytest.mark.asyncio
    async def test_ralph_loop_not_found(self, client: AsyncClient) -> None:
        resp = await client.post(
            f"/agents/ralph-loop/{uuid.uuid4()}/start",
            json={},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_ralph_loop_approve_not_found(self, client: AsyncClient) -> None:
        resp = await client.post(
            f"/agents/ralph-loop/{uuid.uuid4()}/approve",
            json={"approved": True},
        )
        assert resp.status_code == 404
