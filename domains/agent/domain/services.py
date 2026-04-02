"""Agent domain services — SubAgentExecutor and RalphLoopRunner."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

# ---------- SubAgent execution contracts ----------


@dataclass
class SubAgentTask:
    agent_name: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class SubAgentResult:
    agent_name: str
    success: bool
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class SubAgentRunner(Protocol):
    """Protocol that the actual LLM/tool runner must implement."""

    async def invoke(self, task: SubAgentTask) -> SubAgentResult: ...


class SubAgentExecutor:
    """Run sub-agents in parallel with concurrency control."""

    def __init__(self, runner: SubAgentRunner, max_concurrent: int = 8) -> None:
        self.runner = runner
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def run_single(self, task: SubAgentTask) -> SubAgentResult:
        async with self.semaphore:
            return await self.runner.invoke(task)

    async def run_parallel(self, tasks: list[SubAgentTask]) -> list[SubAgentResult]:
        coros = [self.run_single(task) for task in tasks]
        return list(await asyncio.gather(*coros))


# ---------- Ralph Loop contracts ----------


class QualityChecker(Protocol):
    """Evaluates presentation quality, returning checklist items."""

    async def check(self, presentation_id: uuid.UUID) -> list[dict[str, Any]]:
        """Return list of {criterion, weight, passed, details}."""
        ...


class AutoFixer(Protocol):
    """Dispatches fix tasks based on failed criteria."""

    async def fix(self, presentation_id: uuid.UUID, criterion: str) -> bool:
        """Attempt to fix a criterion. Return True if fixed."""
        ...


@dataclass
class RalphLoopRunner:
    """Orchestrates the iterative quality-improvement loop."""

    checker: QualityChecker
    fixer: AutoFixer
    max_iterations: int = 5
    threshold: float = 0.95
    auto_fix_enabled: bool = True

    async def run(self, presentation_id: uuid.UUID) -> list[dict[str, Any]]:
        """Run the loop until threshold met or max iterations.

        Returns list of iteration result dicts.
        """
        iterations: list[dict[str, Any]] = []

        for i in range(1, self.max_iterations + 1):
            raw_results = await self.checker.check(presentation_id)
            total_weight = sum(r["weight"] for r in raw_results) or 1.0
            passed_weight = sum(r["weight"] for r in raw_results if r["passed"])
            score = passed_weight / total_weight

            action = "check_only"

            if score >= self.threshold:
                action = "threshold_met"
                iterations.append(
                    {
                        "iteration_number": i,
                        "score": score,
                        "results": raw_results,
                        "action": action,
                    }
                )
                break

            if self.auto_fix_enabled:
                failed = [r for r in raw_results if not r["passed"]]
                for item in failed:
                    await self.fixer.fix(presentation_id, item["criterion"])
                action = "auto_fix"

            iterations.append(
                {
                    "iteration_number": i,
                    "score": score,
                    "results": raw_results,
                    "action": action,
                }
            )

        return iterations
