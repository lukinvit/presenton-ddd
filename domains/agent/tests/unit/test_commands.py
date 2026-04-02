"""Tests for agent application commands and queries."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest

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
from domains.agent.domain.entities import Agent, AgentPipeline, AgentRun, RalphLoop
from domains.agent.domain.services import SubAgentExecutor, SubAgentResult, SubAgentTask
from domains.agent.domain.value_objects import AgentConfig, RunStatus
from shared.domain.events import DomainEvent

# ---------- In-memory repositories ----------


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
        return SubAgentResult(
            agent_name=task.agent_name,
            success=True,
            result={"output": f"{task.agent_name} done"},
        )


class FailRunner:
    async def invoke(self, task: SubAgentTask) -> SubAgentResult:
        return SubAgentResult(
            agent_name=task.agent_name,
            success=False,
            error=f"{task.agent_name} exploded",
        )


# ---------- Tests ----------


class TestRunPipelineCommand:
    @pytest.mark.asyncio
    async def test_successful_pipeline(self) -> None:
        run_repo = InMemoryAgentRunRepo()
        pipeline_repo = InMemoryAgentPipelineRepo()
        agent_repo = InMemoryAgentRepo()
        event_bus = InMemoryEventBus()
        executor = SubAgentExecutor(runner=SuccessRunner(), max_concurrent=4)

        cmd = RunPipelineCommand(
            run_repo=run_repo,
            pipeline_repo=pipeline_repo,
            agent_repo=agent_repo,
            executor=executor,
            event_bus=event_bus,
        )
        pres_id = uuid.uuid4()
        result = await cmd.execute(topic="AI trends", presentation_id=pres_id)

        assert result.status == "completed"
        assert result.current_stage == "EXPORT"
        assert len(result.sub_agent_runs) > 0
        assert len(event_bus.events) >= 1

    @pytest.mark.asyncio
    async def test_pipeline_fails_on_subagent_error(self) -> None:
        run_repo = InMemoryAgentRunRepo()
        pipeline_repo = InMemoryAgentPipelineRepo()
        agent_repo = InMemoryAgentRepo()
        event_bus = InMemoryEventBus()
        executor = SubAgentExecutor(runner=FailRunner(), max_concurrent=4)

        cmd = RunPipelineCommand(
            run_repo=run_repo,
            pipeline_repo=pipeline_repo,
            agent_repo=agent_repo,
            executor=executor,
            event_bus=event_bus,
        )
        result = await cmd.execute(topic="Test", presentation_id=uuid.uuid4())
        assert result.status == "failed"

    @pytest.mark.asyncio
    async def test_pipeline_stage_progression(self) -> None:
        """Verify that all default pipeline stages are executed in order."""
        stages_visited: list[str] = []
        run_repo = InMemoryAgentRunRepo()

        class TrackingRunRepo:
            async def get(self, id: uuid.UUID) -> AgentRun | None:
                return await run_repo.get(id)

            async def save(self, run: AgentRun) -> None:
                if run.current_stage and (
                    not stages_visited or stages_visited[-1] != run.current_stage
                ):
                    stages_visited.append(run.current_stage)
                await run_repo.save(run)

        pipeline_repo = InMemoryAgentPipelineRepo()
        agent_repo = InMemoryAgentRepo()
        event_bus = InMemoryEventBus()
        executor = SubAgentExecutor(runner=SuccessRunner(), max_concurrent=4)

        cmd = RunPipelineCommand(
            run_repo=TrackingRunRepo(),
            pipeline_repo=pipeline_repo,
            agent_repo=agent_repo,
            executor=executor,
            event_bus=event_bus,
        )
        await cmd.execute(topic="Test", presentation_id=uuid.uuid4())

        expected = [
            "RESEARCH",
            "PLANNING",
            "CONTENT",
            "ASSEMBLY",
            "RENDERING",
            "RALPH_LOOP",
            "EXPORT",
        ]
        assert stages_visited == expected


class TestConfigureAgentCommand:
    @pytest.mark.asyncio
    async def test_configure_new_agent(self) -> None:
        agent_repo = InMemoryAgentRepo()
        cmd = ConfigureAgentCommand(agent_repo=agent_repo)
        result = await cmd.execute(agent_name="ContentWriter", model="gpt-4o")
        assert result.name == "ContentWriter"
        assert result.config.model == "gpt-4o"
        # Should keep default provider
        assert result.config.provider == "anthropic"

    @pytest.mark.asyncio
    async def test_update_existing_agent(self) -> None:
        agent_repo = InMemoryAgentRepo()
        agent = Agent(
            id=uuid.uuid4(),
            name="ContentWriter",
            config=AgentConfig(model="claude-sonnet-4-6", temperature=0.7),
        )
        await agent_repo.save(agent)

        cmd = ConfigureAgentCommand(agent_repo=agent_repo)
        result = await cmd.execute(agent_name="ContentWriter", temperature=0.3)
        assert result.config.temperature == 0.3
        assert result.config.model == "claude-sonnet-4-6"  # unchanged


class TestStartRalphLoopCommand:
    @pytest.mark.asyncio
    async def test_start_loop(self) -> None:
        run_repo = InMemoryAgentRunRepo()
        ralph_repo = InMemoryRalphLoopRepo()
        event_bus = InMemoryEventBus()

        run = AgentRun(id=uuid.uuid4(), status=RunStatus.RUNNING)
        await run_repo.save(run)

        cmd = StartRalphLoopCommand(ralph_repo=ralph_repo, run_repo=run_repo, event_bus=event_bus)
        result = await cmd.execute(agent_run_id=run.id)
        assert result.status == "running"
        assert result.agent_run_id == str(run.id)

        # Run should be in waiting_approval
        updated_run = await run_repo.get(run.id)
        assert updated_run is not None
        assert updated_run.status == RunStatus.WAITING_APPROVAL

    @pytest.mark.asyncio
    async def test_start_loop_missing_run(self) -> None:
        ralph_repo = InMemoryRalphLoopRepo()
        run_repo = InMemoryAgentRunRepo()
        event_bus = InMemoryEventBus()
        cmd = StartRalphLoopCommand(ralph_repo=ralph_repo, run_repo=run_repo, event_bus=event_bus)
        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(agent_run_id=uuid.uuid4())


class TestApproveRalphLoopCommand:
    @pytest.mark.asyncio
    async def test_approve(self) -> None:
        run_repo = InMemoryAgentRunRepo()
        ralph_repo = InMemoryRalphLoopRepo()
        event_bus = InMemoryEventBus()

        run = AgentRun(id=uuid.uuid4(), status=RunStatus.WAITING_APPROVAL)
        await run_repo.save(run)

        loop = RalphLoop(id=uuid.uuid4(), agent_run_id=run.id)
        await ralph_repo.save(loop)

        cmd = ApproveRalphLoopCommand(ralph_repo=ralph_repo, run_repo=run_repo, event_bus=event_bus)
        result = await cmd.execute(ralph_loop_id=loop.id, approved=True)
        assert result.status == "approved"

        updated_run = await run_repo.get(run.id)
        assert updated_run is not None
        assert updated_run.status == RunStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_reject_with_feedback(self) -> None:
        run_repo = InMemoryAgentRunRepo()
        ralph_repo = InMemoryRalphLoopRepo()
        event_bus = InMemoryEventBus()

        run = AgentRun(id=uuid.uuid4(), status=RunStatus.WAITING_APPROVAL)
        await run_repo.save(run)

        loop = RalphLoop(id=uuid.uuid4(), agent_run_id=run.id)
        await ralph_repo.save(loop)

        cmd = ApproveRalphLoopCommand(ralph_repo=ralph_repo, run_repo=run_repo, event_bus=event_bus)
        result = await cmd.execute(ralph_loop_id=loop.id, approved=False, feedback="Fix colors")
        assert result.status == "running"
        assert len(result.iterations) == 1
        assert result.iterations[0].action_taken == "human_feedback"


# ---------- Query tests ----------


class TestGetAgentRunQuery:
    @pytest.mark.asyncio
    async def test_get_existing(self) -> None:
        run_repo = InMemoryAgentRunRepo()
        run = AgentRun(id=uuid.uuid4(), status=RunStatus.RUNNING, current_stage="CONTENT")
        await run_repo.save(run)

        query = GetAgentRunQuery(run_repo=run_repo)
        result = await query.execute(run.id)
        assert result.id == str(run.id)
        assert result.status == "running"

    @pytest.mark.asyncio
    async def test_get_not_found(self) -> None:
        query = GetAgentRunQuery(run_repo=InMemoryAgentRunRepo())
        with pytest.raises(ValueError, match="not found"):
            await query.execute(uuid.uuid4())


class TestListAgentsQuery:
    @pytest.mark.asyncio
    async def test_list_defaults(self) -> None:
        query = ListAgentsQuery(agent_repo=InMemoryAgentRepo())
        results = await query.execute()
        assert len(results) == 13
        names = {a.name for a in results}
        assert "Orchestrator" in names
        assert "ContentWriter" in names
        assert "QualityReviewer" in names

    @pytest.mark.asyncio
    async def test_list_configured(self) -> None:
        agent_repo = InMemoryAgentRepo()
        agent = Agent(id=uuid.uuid4(), name="Custom", config=AgentConfig(model="custom-model"))
        await agent_repo.save(agent)

        query = ListAgentsQuery(agent_repo=agent_repo)
        results = await query.execute()
        assert len(results) == 1
        assert results[0].name == "Custom"


class TestGetRalphLoopStatusQuery:
    @pytest.mark.asyncio
    async def test_get_status(self) -> None:
        ralph_repo = InMemoryRalphLoopRepo()
        loop = RalphLoop(id=uuid.uuid4(), agent_run_id=uuid.uuid4())
        await ralph_repo.save(loop)

        query = GetRalphLoopStatusQuery(ralph_repo=ralph_repo)
        result = await query.execute(loop.id)
        assert result.status == "running"
        assert result.current_score == 0.0
