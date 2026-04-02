"""Tests for agent domain services — SubAgentExecutor and RalphLoopRunner."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any

import pytest

from domains.agent.domain.services import (
    RalphLoopRunner,
    SubAgentExecutor,
    SubAgentResult,
    SubAgentTask,
)

# ---------- Mock runner for SubAgentExecutor ----------


@dataclass
class MockSubAgentRunner:
    delay: float = 0.01
    fail_agents: set[str] = field(default_factory=set)
    call_log: list[str] = field(default_factory=list)

    async def invoke(self, task: SubAgentTask) -> SubAgentResult:
        self.call_log.append(task.agent_name)
        await asyncio.sleep(self.delay)
        if task.agent_name in self.fail_agents:
            return SubAgentResult(
                agent_name=task.agent_name,
                success=False,
                error=f"{task.agent_name} failed",
            )
        return SubAgentResult(
            agent_name=task.agent_name,
            success=True,
            result={"agent": task.agent_name, "status": "done"},
        )


class TestSubAgentExecutor:
    @pytest.mark.asyncio
    async def test_run_single(self) -> None:
        runner = MockSubAgentRunner()
        executor = SubAgentExecutor(runner=runner, max_concurrent=4)
        task = SubAgentTask(agent_name="ContentWriter", payload={"topic": "AI"})
        result = await executor.run_single(task)
        assert result.success is True
        assert result.agent_name == "ContentWriter"
        assert result.result["status"] == "done"

    @pytest.mark.asyncio
    async def test_run_parallel_all_succeed(self) -> None:
        runner = MockSubAgentRunner()
        executor = SubAgentExecutor(runner=runner, max_concurrent=4)
        tasks = [
            SubAgentTask(agent_name="ContentWriter"),
            SubAgentTask(agent_name="PaletteDesigner"),
            SubAgentTask(agent_name="FontSelector"),
        ]
        results = await executor.run_parallel(tasks)
        assert len(results) == 3
        assert all(r.success for r in results)
        names = {r.agent_name for r in results}
        assert names == {"ContentWriter", "PaletteDesigner", "FontSelector"}

    @pytest.mark.asyncio
    async def test_run_parallel_with_failure(self) -> None:
        runner = MockSubAgentRunner(fail_agents={"PaletteDesigner"})
        executor = SubAgentExecutor(runner=runner, max_concurrent=4)
        tasks = [
            SubAgentTask(agent_name="ContentWriter"),
            SubAgentTask(agent_name="PaletteDesigner"),
        ]
        results = await executor.run_parallel(tasks)
        assert len(results) == 2
        success = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        assert len(success) == 1
        assert len(failed) == 1
        assert failed[0].agent_name == "PaletteDesigner"
        assert failed[0].error == "PaletteDesigner failed"

    @pytest.mark.asyncio
    async def test_concurrency_limit(self) -> None:
        """Verify semaphore limits concurrent executions."""
        active = 0
        max_active = 0

        class ConcurrencyTracker:
            async def invoke(self, task: SubAgentTask) -> SubAgentResult:
                nonlocal active, max_active
                active += 1
                max_active = max(max_active, active)
                await asyncio.sleep(0.02)
                active -= 1
                return SubAgentResult(agent_name=task.agent_name, success=True)

        executor = SubAgentExecutor(runner=ConcurrencyTracker(), max_concurrent=2)
        tasks = [SubAgentTask(agent_name=f"agent_{i}") for i in range(6)]
        results = await executor.run_parallel(tasks)
        assert len(results) == 6
        assert max_active <= 2

    @pytest.mark.asyncio
    async def test_run_parallel_preserves_order(self) -> None:
        runner = MockSubAgentRunner(delay=0.001)
        executor = SubAgentExecutor(runner=runner, max_concurrent=8)
        tasks = [SubAgentTask(agent_name=f"agent_{i}") for i in range(5)]
        results = await executor.run_parallel(tasks)
        assert [r.agent_name for r in results] == [f"agent_{i}" for i in range(5)]


# ---------- Mock checker/fixer for RalphLoopRunner ----------


@dataclass
class MockQualityChecker:
    results_per_call: list[list[dict[str, Any]]] = field(default_factory=list)
    _call_count: int = 0

    async def check(self, presentation_id: uuid.UUID) -> list[dict[str, Any]]:
        if self._call_count < len(self.results_per_call):
            result = self.results_per_call[self._call_count]
        else:
            result = self.results_per_call[-1] if self.results_per_call else []
        self._call_count += 1
        return result


@dataclass
class MockAutoFixer:
    fixed_criteria: set[str] = field(default_factory=set)
    fix_log: list[str] = field(default_factory=list)

    async def fix(self, presentation_id: uuid.UUID, criterion: str) -> bool:
        self.fix_log.append(criterion)
        self.fixed_criteria.add(criterion)
        return True


class TestRalphLoopRunner:
    @pytest.mark.asyncio
    async def test_threshold_met_first_iteration(self) -> None:
        checker = MockQualityChecker(
            results_per_call=[
                [
                    {
                        "criterion": "color_consistency",
                        "weight": 1.0,
                        "passed": True,
                        "details": "",
                    },
                    {"criterion": "font_hierarchy", "weight": 1.0, "passed": True, "details": ""},
                ]
            ]
        )
        fixer = MockAutoFixer()
        runner = RalphLoopRunner(checker=checker, fixer=fixer, max_iterations=5, threshold=0.95)
        iterations = await runner.run(uuid.uuid4())
        assert len(iterations) == 1
        assert iterations[0]["action"] == "threshold_met"
        assert iterations[0]["score"] == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_auto_fix_then_pass(self) -> None:
        checker = MockQualityChecker(
            results_per_call=[
                [
                    {"criterion": "c1", "weight": 1.0, "passed": True, "details": ""},
                    {"criterion": "c2", "weight": 1.0, "passed": False, "details": "bad"},
                ],
                [
                    {"criterion": "c1", "weight": 1.0, "passed": True, "details": ""},
                    {"criterion": "c2", "weight": 1.0, "passed": True, "details": "fixed"},
                ],
            ]
        )
        fixer = MockAutoFixer()
        runner = RalphLoopRunner(checker=checker, fixer=fixer, max_iterations=5, threshold=0.95)
        iterations = await runner.run(uuid.uuid4())
        assert len(iterations) == 2
        assert iterations[0]["action"] == "auto_fix"
        assert iterations[0]["score"] == pytest.approx(0.5)
        assert iterations[1]["action"] == "threshold_met"
        assert iterations[1]["score"] == pytest.approx(1.0)
        assert "c2" in fixer.fix_log

    @pytest.mark.asyncio
    async def test_max_iterations_exhausted(self) -> None:
        always_fail = [
            {"criterion": "c1", "weight": 1.0, "passed": False, "details": "fail"},
        ]
        checker = MockQualityChecker(results_per_call=[always_fail])
        fixer = MockAutoFixer()
        runner = RalphLoopRunner(checker=checker, fixer=fixer, max_iterations=3, threshold=0.95)
        iterations = await runner.run(uuid.uuid4())
        assert len(iterations) == 3
        assert all(it["action"] == "auto_fix" for it in iterations)

    @pytest.mark.asyncio
    async def test_auto_fix_disabled(self) -> None:
        checker = MockQualityChecker(
            results_per_call=[[{"criterion": "c1", "weight": 1.0, "passed": False, "details": ""}]]
        )
        fixer = MockAutoFixer()
        runner = RalphLoopRunner(
            checker=checker,
            fixer=fixer,
            max_iterations=2,
            threshold=0.95,
            auto_fix_enabled=False,
        )
        iterations = await runner.run(uuid.uuid4())
        assert len(iterations) == 2
        assert all(it["action"] == "check_only" for it in iterations)
        assert fixer.fix_log == []
