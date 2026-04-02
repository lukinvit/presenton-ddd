"""Unit tests for rendering application commands."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.rendering.application.commands import (
    BatchRenderCommand,
    ComputeVisualDiffCommand,
    RenderPresentationCommand,
    RenderSlideCommand,
)
from domains.rendering.application.dto import RenderedSlideDTO, RenderJobDTO, VisualDiffResultDTO
from domains.rendering.domain.entities import RenderJob
from domains.rendering.domain.value_objects import RenderConfig, RenderStatus

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_html_renderer(html: str = "<div>slide</div>") -> AsyncMock:
    renderer = AsyncMock()
    renderer.render = AsyncMock(return_value=html)
    return renderer


def _make_repo(job: RenderJob | None = None) -> AsyncMock:
    repo = AsyncMock()
    repo.get = AsyncMock(return_value=job)
    repo.save = AsyncMock()
    repo.list_all = AsyncMock(return_value=[])
    return repo


# ---------------------------------------------------------------------------
# RenderSlideCommand
# ---------------------------------------------------------------------------


class TestRenderSlideCommand:
    async def test_renders_slide(self) -> None:
        renderer = _make_html_renderer("<h1>Hello</h1>")
        cmd = RenderSlideCommand(html_renderer=renderer)
        slide_id = uuid.uuid4()
        result = await cmd.execute(
            slide_id=slide_id,
            slide_data={"title": "Hello"},
            css_variables="--color: red;",
        )
        assert isinstance(result, RenderedSlideDTO)
        assert result.slide_id == str(slide_id)
        assert result.html == "<h1>Hello</h1>"
        assert result.render_time_ms >= 0
        renderer.render.assert_awaited_once_with({"title": "Hello"}, "--color: red;")

    async def test_uses_custom_config(self) -> None:
        renderer = _make_html_renderer()
        cmd = RenderSlideCommand(html_renderer=renderer)
        config = RenderConfig(width=1280, height=720)
        result = await cmd.execute(
            slide_id=uuid.uuid4(),
            slide_data={},
            css_variables="",
            config=config,
        )
        assert isinstance(result, RenderedSlideDTO)

    async def test_default_config_used_when_none(self) -> None:
        renderer = _make_html_renderer()
        cmd = RenderSlideCommand(html_renderer=renderer)
        result = await cmd.execute(
            slide_id=uuid.uuid4(),
            slide_data={},
            css_variables="",
            config=None,
        )
        assert result.html is not None


# ---------------------------------------------------------------------------
# RenderPresentationCommand
# ---------------------------------------------------------------------------


class TestRenderPresentationCommand:
    async def test_creates_completed_job(self) -> None:
        renderer = _make_html_renderer("<p>slide</p>")
        repo = _make_repo()
        presentation_id = uuid.uuid4()
        slide_id = uuid.uuid4()
        slides_data = [{"slide_id": str(slide_id), "data": {"title": "Intro"}}]

        cmd = RenderPresentationCommand(repo=repo, html_renderer=renderer)
        result = await cmd.execute(
            presentation_id=presentation_id,
            slides_data=slides_data,
            css_variables="--bg: white;",
        )

        assert isinstance(result, RenderJobDTO)
        assert result.presentation_id == str(presentation_id)
        assert result.status == RenderStatus.COMPLETED.value
        assert len(result.rendered_slides) == 1
        assert result.rendered_slides[0].html == "<p>slide</p>"
        assert result.completed_at is not None
        # repo.save called at least twice (initial + final)
        assert repo.save.await_count >= 2

    async def test_marks_failed_on_renderer_error(self) -> None:
        renderer = AsyncMock()
        renderer.render = AsyncMock(side_effect=RuntimeError("boom"))
        repo = _make_repo()
        cmd = RenderPresentationCommand(repo=repo, html_renderer=renderer)

        with pytest.raises(RuntimeError, match="boom"):
            await cmd.execute(
                presentation_id=uuid.uuid4(),
                slides_data=[{"slide_id": str(uuid.uuid4()), "data": {}}],
                css_variables="",
            )
        # The saved job should be in FAILED status
        saved_job: RenderJob = repo.save.call_args_list[-1][0][0]
        assert saved_job.status == RenderStatus.FAILED

    async def test_empty_slides_data(self) -> None:
        renderer = _make_html_renderer()
        repo = _make_repo()
        cmd = RenderPresentationCommand(repo=repo, html_renderer=renderer)
        result = await cmd.execute(
            presentation_id=uuid.uuid4(),
            slides_data=[],
            css_variables="",
        )
        assert result.status == RenderStatus.COMPLETED.value
        assert result.rendered_slides == []


# ---------------------------------------------------------------------------
# BatchRenderCommand
# ---------------------------------------------------------------------------


class TestBatchRenderCommand:
    async def test_renders_existing_job(self) -> None:
        renderer = _make_html_renderer("<section/>")
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        repo = _make_repo(job)
        slide_id = uuid.uuid4()

        cmd = BatchRenderCommand(
            repo=repo,
            html_renderer=renderer,
            slides_data=[{"slide_id": str(slide_id), "data": {}}],
            css_variables="",
        )
        result = await cmd.execute(render_job_id=job.id)

        assert result.status == RenderStatus.COMPLETED.value
        assert len(result.rendered_slides) == 1

    async def test_raises_if_job_not_found(self) -> None:
        renderer = _make_html_renderer()
        repo = _make_repo(None)
        cmd = BatchRenderCommand(repo=repo, html_renderer=renderer)

        with pytest.raises(ValueError, match="not found"):
            await cmd.execute(render_job_id=uuid.uuid4())

    async def test_marks_failed_on_error(self) -> None:
        renderer = AsyncMock()
        renderer.render = AsyncMock(side_effect=RuntimeError("fail"))
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        repo = _make_repo(job)

        cmd = BatchRenderCommand(
            repo=repo,
            html_renderer=renderer,
            slides_data=[{"slide_id": str(uuid.uuid4()), "data": {}}],
        )
        with pytest.raises(RuntimeError):
            await cmd.execute(render_job_id=job.id)

        saved_job: RenderJob = repo.save.call_args_list[-1][0][0]
        assert saved_job.status == RenderStatus.FAILED


# ---------------------------------------------------------------------------
# ComputeVisualDiffCommand
# ---------------------------------------------------------------------------


class TestComputeVisualDiffCommand:
    async def test_identical_images_return_zero_diff(self) -> None:
        cmd = ComputeVisualDiffCommand()
        slide_id = uuid.uuid4()
        img = b"\x00\x01\x02\x03"
        result = await cmd.execute(slide_id=slide_id, image_a=img, image_b=img)

        assert isinstance(result, VisualDiffResultDTO)
        assert result.slide_id == str(slide_id)
        assert result.difference_percent == 0.0
        assert result.changed_regions == []

    async def test_different_images_return_nonzero_diff(self) -> None:
        cmd = ComputeVisualDiffCommand()
        slide_id = uuid.uuid4()
        result = await cmd.execute(
            slide_id=slide_id,
            image_a=b"\x00\x01\x02",
            image_b=b"\xff\xfe\xfd",
        )
        assert result.difference_percent > 0.0
        assert len(result.changed_regions) > 0

    async def test_uses_injected_diff_service(self) -> None:
        mock_service = MagicMock()
        mock_service.compute_diff.return_value = MagicMock(
            slide_id=uuid.uuid4(),
            difference_percent=25.0,
            changed_regions=["header"],
        )
        cmd = ComputeVisualDiffCommand(diff_service=mock_service)
        slide_id = uuid.uuid4()
        result = await cmd.execute(slide_id=slide_id, image_a=b"a", image_b=b"b")

        assert result.difference_percent == 25.0
        assert result.changed_regions == ["header"]
        mock_service.compute_diff.assert_called_once()
