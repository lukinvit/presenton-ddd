"""Tests for agent domain entities and value objects."""

from __future__ import annotations

import uuid

import pytest

from domains.agent.domain.entities import (
    Agent,
    AgentPipeline,
    AgentRun,
    RalphLoop,
    SubAgentRun,
)
from domains.agent.domain.value_objects import (
    AgentConfig,
    ChecklistItem,
    PipelineConfig,
    PipelineStage,
    RalphIteration,
    RalphLoopConfig,
    RunStatus,
)

# ---------- Value Objects ----------


class TestRunStatus:
    def test_enum_values(self) -> None:
        assert RunStatus.PENDING.value == "pending"
        assert RunStatus.RUNNING.value == "running"
        assert RunStatus.COMPLETED.value == "completed"
        assert RunStatus.FAILED.value == "failed"
        assert RunStatus.WAITING_APPROVAL.value == "waiting_approval"


class TestAgentConfig:
    def test_defaults(self) -> None:
        cfg = AgentConfig()
        assert cfg.model == ""
        assert cfg.provider == "anthropic"
        assert cfg.temperature == 0.7
        assert cfg.max_tokens == 4096
        assert cfg.tools == ()

    def test_frozen(self) -> None:
        cfg = AgentConfig(model="claude-sonnet-4-6")
        with pytest.raises(AttributeError):
            cfg.model = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        a = AgentConfig(model="m1", provider="p1")
        b = AgentConfig(model="m1", provider="p1")
        assert a == b


class TestPipelineStage:
    def test_creation(self) -> None:
        stage = PipelineStage(name="RESEARCH", agents=("WebResearcher",), parallel=False)
        assert stage.name == "RESEARCH"
        assert stage.agents == ("WebResearcher",)
        assert stage.parallel is False


class TestPipelineConfig:
    def test_defaults(self) -> None:
        cfg = PipelineConfig()
        assert cfg.parallel_subagents is True
        assert cfg.max_concurrent == 8


class TestRalphLoopConfig:
    def test_defaults(self) -> None:
        cfg = RalphLoopConfig()
        assert cfg.max_iterations == 5
        assert cfg.threshold == 0.95
        assert cfg.auto_fix_enabled is True
        assert cfg.human_approval_required is True
        assert cfg.checklist_weights == {}


class TestChecklistItem:
    def test_creation(self) -> None:
        item = ChecklistItem(criterion="color_consistency", weight=2.0, passed=True, details="ok")
        assert item.criterion == "color_consistency"
        assert item.weight == 2.0
        assert item.passed is True


class TestRalphIteration:
    def test_creation(self) -> None:
        items = (ChecklistItem(criterion="c1", weight=1.0, passed=True, details="ok"),)
        it = RalphIteration(
            iteration_number=1,
            checklist_results=items,
            weighted_score=1.0,
            action_taken="auto_fix",
        )
        assert it.iteration_number == 1
        assert it.weighted_score == 1.0


# ---------- Entities ----------


class TestAgent:
    def test_creation(self) -> None:
        agent = Agent(
            id=uuid.uuid4(),
            name="ContentWriter",
            config=AgentConfig(model="claude-sonnet-4-6"),
        )
        assert agent.name == "ContentWriter"
        assert agent.enabled is True


class TestSubAgentRun:
    def test_lifecycle(self) -> None:
        sr = SubAgentRun(id=uuid.uuid4(), agent_name="ContentWriter")
        assert sr.status == RunStatus.PENDING

        sr.start()
        assert sr.status == RunStatus.RUNNING

        sr.complete({"output": "done"})
        assert sr.status == RunStatus.COMPLETED
        assert sr.result == {"output": "done"}
        assert sr.completed_at is not None

    def test_fail(self) -> None:
        sr = SubAgentRun(id=uuid.uuid4(), agent_name="ContentWriter")
        sr.start()
        sr.fail("timeout")
        assert sr.status == RunStatus.FAILED
        assert sr.error == "timeout"
        assert sr.completed_at is not None


class TestAgentRun:
    def test_lifecycle(self) -> None:
        run = AgentRun(id=uuid.uuid4())
        assert run.status == RunStatus.PENDING

        run.start()
        assert run.status == RunStatus.RUNNING

        run.set_stage("RESEARCH")
        assert run.current_stage == "RESEARCH"

        run.complete()
        assert run.status == RunStatus.COMPLETED
        assert run.completed_at is not None

    def test_fail(self) -> None:
        run = AgentRun(id=uuid.uuid4())
        run.start()
        run.fail()
        assert run.status == RunStatus.FAILED

    def test_wait_approval(self) -> None:
        run = AgentRun(id=uuid.uuid4())
        run.start()
        run.wait_approval()
        assert run.status == RunStatus.WAITING_APPROVAL

    def test_add_sub_agent_run(self) -> None:
        run = AgentRun(id=uuid.uuid4())
        sr = SubAgentRun(id=uuid.uuid4(), agent_name="Writer")
        run.add_sub_agent_run(sr)
        assert len(run.sub_agent_runs) == 1


class TestRalphLoop:
    def test_add_iteration_calculates_score(self) -> None:
        loop = RalphLoop(id=uuid.uuid4())
        items = [
            ChecklistItem(criterion="c1", weight=2.0, passed=True, details=""),
            ChecklistItem(criterion="c2", weight=2.0, passed=False, details="bad"),
        ]
        iteration = loop.add_iteration(items, action_taken="auto_fix")
        assert iteration.iteration_number == 1
        assert iteration.weighted_score == pytest.approx(0.5)
        assert loop.current_score == pytest.approx(0.5)

    def test_meets_threshold(self) -> None:
        loop = RalphLoop(
            id=uuid.uuid4(),
            config=RalphLoopConfig(threshold=0.8),
        )
        items = [ChecklistItem(criterion="c1", weight=1.0, passed=True, details="")]
        loop.add_iteration(items, action_taken="check_only")
        assert loop.meets_threshold() is True

    def test_max_iterations_reached(self) -> None:
        loop = RalphLoop(
            id=uuid.uuid4(),
            config=RalphLoopConfig(max_iterations=2),
        )
        items = [ChecklistItem(criterion="c1", weight=1.0, passed=False, details="")]
        loop.add_iteration(items, action_taken="auto_fix")
        assert loop.max_iterations_reached() is False
        loop.add_iteration(items, action_taken="auto_fix")
        assert loop.max_iterations_reached() is True

    def test_approve_and_reject(self) -> None:
        loop = RalphLoop(id=uuid.uuid4())
        assert loop.status == "running"
        loop.approve()
        assert loop.status == "approved"
        loop.reject_with_feedback()
        assert loop.status == "running"

    def test_failed_criteria(self) -> None:
        loop = RalphLoop(id=uuid.uuid4())
        items = [
            ChecklistItem(criterion="c1", weight=1.0, passed=True, details=""),
            ChecklistItem(criterion="c2", weight=1.0, passed=False, details="fail"),
        ]
        loop.add_iteration(items, action_taken="check_only")
        failed = loop.failed_criteria()
        assert len(failed) == 1
        assert failed[0].criterion == "c2"

    def test_empty_iterations(self) -> None:
        loop = RalphLoop(id=uuid.uuid4())
        assert loop.current_score == 0.0
        assert loop.iteration_count == 0
        assert loop.failed_criteria() == []


class TestAgentPipeline:
    def test_creation(self) -> None:
        pipeline = AgentPipeline(
            id=uuid.uuid4(),
            name="default",
            stages=[
                PipelineStage(name="RESEARCH", agents=("WebResearcher",)),
            ],
            config=PipelineConfig(),
        )
        assert pipeline.name == "default"
        assert len(pipeline.stages) == 1
