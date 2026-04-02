"""Agent application commands."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from domains.agent.application.dto import (
    AgentConfigDTO,
    AgentDTO,
    AgentRunDTO,
    ChecklistItemDTO,
    RalphIterationDTO,
    RalphLoopDTO,
    SubAgentRunDTO,
)
from domains.agent.domain.defaults import DEFAULT_AGENTS, DEFAULT_PIPELINE_STAGES
from domains.agent.domain.entities import (
    Agent,
    AgentPipeline,
    AgentRun,
    RalphLoop,
    SubAgentRun,
)
from domains.agent.domain.events import (
    EVENT_PIPELINE_STARTED,
    EVENT_RALPH_LOOP_APPROVED,
    EVENT_RALPH_LOOP_STARTED,
)
from domains.agent.domain.repositories import (
    AgentPipelineRepository,
    AgentRepository,
    AgentRunRepository,
    RalphLoopRepository,
)
from domains.agent.domain.services import (
    SubAgentExecutor,
    SubAgentTask,
)
from domains.agent.domain.value_objects import (
    AgentConfig,
    ChecklistItem,
    PipelineConfig,
    RalphLoopConfig,
)
from shared.domain.events import DomainEvent, EventBus

# ---------- helpers ----------


def _agent_to_dto(agent: Agent) -> AgentDTO:
    return AgentDTO(
        id=str(agent.id),
        name=agent.name,
        config=AgentConfigDTO(
            model=agent.config.model,
            provider=agent.config.provider,
            system_prompt=agent.config.system_prompt,
            temperature=agent.config.temperature,
            max_tokens=agent.config.max_tokens,
            tools=list(agent.config.tools),
        ),
        enabled=agent.enabled,
    )


def _sub_run_to_dto(sr: SubAgentRun) -> SubAgentRunDTO:
    return SubAgentRunDTO(
        id=str(sr.id),
        agent_name=sr.agent_name,
        status=sr.status.value,
        result=sr.result,
        error=sr.error,
        started_at=sr.started_at.isoformat(),
        completed_at=sr.completed_at.isoformat() if sr.completed_at else None,
    )


def _run_to_dto(run: AgentRun) -> AgentRunDTO:
    return AgentRunDTO(
        id=str(run.id),
        pipeline_id=str(run.pipeline_id),
        presentation_id=str(run.presentation_id),
        status=run.status.value,
        current_stage=run.current_stage,
        sub_agent_runs=[_sub_run_to_dto(sr) for sr in run.sub_agent_runs],
        started_at=run.started_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )


def _ralph_loop_to_dto(loop: RalphLoop) -> RalphLoopDTO:
    return RalphLoopDTO(
        id=str(loop.id),
        agent_run_id=str(loop.agent_run_id),
        status=loop.status,
        iterations=[
            RalphIterationDTO(
                iteration_number=it.iteration_number,
                checklist_results=[
                    ChecklistItemDTO(
                        criterion=ci.criterion,
                        weight=ci.weight,
                        passed=ci.passed,
                        details=ci.details,
                    )
                    for ci in it.checklist_results
                ],
                weighted_score=it.weighted_score,
                action_taken=it.action_taken,
            )
            for it in loop.iterations
        ],
        current_score=loop.current_score,
    )


# ---------- Commands ----------


@dataclass
class RunPipelineCommand:
    run_repo: AgentRunRepository
    pipeline_repo: AgentPipelineRepository
    agent_repo: AgentRepository
    executor: SubAgentExecutor
    event_bus: EventBus

    async def execute(
        self,
        topic: str,
        presentation_id: uuid.UUID,
        pipeline_name: str = "default",
        config: dict[str, Any] | None = None,
    ) -> AgentRunDTO:
        pipeline = await self.pipeline_repo.get_by_name(pipeline_name)
        if pipeline is None:
            pipeline = AgentPipeline(
                id=uuid.uuid4(),
                name="default",
                stages=list(DEFAULT_PIPELINE_STAGES),
                config=PipelineConfig(**(config or {})),
            )
            await self.pipeline_repo.save(pipeline)

        run = AgentRun(
            id=uuid.uuid4(),
            pipeline_id=pipeline.id,
            presentation_id=presentation_id,
        )
        run.start()
        await self.run_repo.save(run)

        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=run.id,
                event_type=EVENT_PIPELINE_STARTED,
                payload={"topic": topic, "presentation_id": str(presentation_id)},
            )
        )

        try:
            for stage in pipeline.stages:
                run.set_stage(stage.name)
                await self.run_repo.save(run)

                tasks = [
                    SubAgentTask(agent_name=name, payload={"topic": topic}) for name in stage.agents
                ]

                if stage.parallel and pipeline.config.parallel_subagents:
                    results = await self.executor.run_parallel(tasks)
                else:
                    results = []
                    for task in tasks:
                        result = await self.executor.run_single(task)
                        results.append(result)

                for res in results:
                    sub_run = SubAgentRun(
                        id=uuid.uuid4(),
                        agent_run_id=run.id,
                        agent_name=res.agent_name,
                    )
                    if res.success:
                        sub_run.complete(res.result)
                    else:
                        sub_run.fail(res.error or "Unknown error")
                    run.add_sub_agent_run(sub_run)

                failed = [r for r in results if not r.success]
                if failed:
                    run.fail()
                    await self.run_repo.save(run)
                    return _run_to_dto(run)

            run.complete()
        except Exception as exc:
            run.fail()
            await self.run_repo.save(run)
            raise RuntimeError(f"Pipeline failed: {exc}") from exc

        await self.run_repo.save(run)
        return _run_to_dto(run)


@dataclass
class ConfigureAgentCommand:
    agent_repo: AgentRepository

    async def execute(
        self,
        agent_name: str,
        model: str | None = None,
        provider: str | None = None,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[str] | None = None,
    ) -> AgentDTO:
        agent = await self.agent_repo.get_by_name(agent_name)
        if agent is None:
            default_cfg = DEFAULT_AGENTS.get(agent_name, AgentConfig())
            agent = Agent(id=uuid.uuid4(), name=agent_name, config=default_cfg)

        new_config = AgentConfig(
            model=model if model is not None else agent.config.model,
            provider=provider if provider is not None else agent.config.provider,
            system_prompt=(
                system_prompt if system_prompt is not None else agent.config.system_prompt
            ),
            temperature=(temperature if temperature is not None else agent.config.temperature),
            max_tokens=(max_tokens if max_tokens is not None else agent.config.max_tokens),
            tools=tuple(tools) if tools is not None else agent.config.tools,
        )
        agent.config = new_config
        await self.agent_repo.save(agent)
        return _agent_to_dto(agent)


@dataclass
class StartRalphLoopCommand:
    ralph_repo: RalphLoopRepository
    run_repo: AgentRunRepository
    event_bus: EventBus

    async def execute(
        self,
        agent_run_id: uuid.UUID,
        config: dict[str, Any] | None = None,
    ) -> RalphLoopDTO:
        run = await self.run_repo.get(agent_run_id)
        if run is None:
            raise ValueError(f"AgentRun '{agent_run_id}' not found")

        loop_config = RalphLoopConfig(**(config or {}))
        loop = RalphLoop(
            id=uuid.uuid4(),
            agent_run_id=agent_run_id,
            config=loop_config,
        )
        await self.ralph_repo.save(loop)

        run.wait_approval()
        await self.run_repo.save(run)

        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=loop.id,
                event_type=EVENT_RALPH_LOOP_STARTED,
                payload={"agent_run_id": str(agent_run_id)},
            )
        )
        return _ralph_loop_to_dto(loop)


@dataclass
class ApproveRalphLoopCommand:
    ralph_repo: RalphLoopRepository
    run_repo: AgentRunRepository
    event_bus: EventBus

    async def execute(
        self,
        ralph_loop_id: uuid.UUID,
        approved: bool,
        feedback: str | None = None,
    ) -> RalphLoopDTO:
        loop = await self.ralph_repo.get(ralph_loop_id)
        if loop is None:
            raise ValueError(f"RalphLoop '{ralph_loop_id}' not found")

        if approved:
            loop.approve()
            # Also complete the parent run
            run = await self.run_repo.get(loop.agent_run_id)
            if run is not None:
                run.complete()
                await self.run_repo.save(run)

            await self.event_bus.publish(
                DomainEvent(
                    aggregate_id=loop.id,
                    event_type=EVENT_RALPH_LOOP_APPROVED,
                    payload={"feedback": feedback},
                )
            )
        else:
            loop.reject_with_feedback()
            if feedback:
                loop.add_iteration(
                    checklist_results=[
                        ChecklistItem(
                            criterion="human_feedback",
                            weight=1.0,
                            passed=False,
                            details=feedback,
                        )
                    ],
                    action_taken="human_feedback",
                )

        await self.ralph_repo.save(loop)
        return _ralph_loop_to_dto(loop)
