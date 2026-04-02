"""Unit tests for rendering domain entities."""

from __future__ import annotations

import uuid

import pytest

from domains.rendering.domain.entities import RenderedSlide, RenderJob
from domains.rendering.domain.value_objects import RenderConfig, RenderStatus


class TestRenderConfig:
    def test_defaults(self) -> None:
        cfg = RenderConfig()
        assert cfg.width == 1920
        assert cfg.height == 1080
        assert cfg.format == "html"
        assert cfg.include_css is True

    def test_custom_values(self) -> None:
        cfg = RenderConfig(width=1280, height=720, format="html", include_css=False)
        assert cfg.width == 1280
        assert cfg.include_css is False

    def test_equality(self) -> None:
        assert RenderConfig() == RenderConfig()
        assert RenderConfig(width=800) != RenderConfig(width=1920)


class TestRenderedSlide:
    def test_creation(self) -> None:
        slide_id = uuid.uuid4()
        s = RenderedSlide(id=uuid.uuid4(), slide_id=slide_id, html="<div/>", render_time_ms=42)
        assert s.slide_id == slide_id
        assert s.html == "<div/>"
        assert s.render_time_ms == 42
        assert s.thumbnail_url is None


class TestRenderJob:
    def test_initial_status_is_pending(self) -> None:
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        assert job.status == RenderStatus.PENDING

    def test_start_rendering_transitions_to_rendering(self) -> None:
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        job.start_rendering()
        assert job.status == RenderStatus.RENDERING

    def test_complete_transitions_to_completed(self) -> None:
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        job.start_rendering()
        job.complete()
        assert job.status == RenderStatus.COMPLETED
        assert job.completed_at is not None

    def test_fail_transitions_to_failed(self) -> None:
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        job.start_rendering()
        job.fail()
        assert job.status == RenderStatus.FAILED
        assert job.completed_at is not None

    def test_start_rendering_from_non_pending_raises(self) -> None:
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        job.start_rendering()
        with pytest.raises(ValueError, match="Cannot start rendering"):
            job.start_rendering()

    def test_complete_from_non_rendering_raises(self) -> None:
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        with pytest.raises(ValueError, match="Cannot complete"):
            job.complete()

    def test_add_and_get_rendered_slide(self) -> None:
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        slide_id = uuid.uuid4()
        rendered = RenderedSlide(id=uuid.uuid4(), slide_id=slide_id, html="<p/>")
        job.add_rendered_slide(rendered)
        assert job.get_rendered_slide(slide_id) is rendered

    def test_get_missing_slide_returns_none(self) -> None:
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        assert job.get_rendered_slide(uuid.uuid4()) is None

    def test_default_config(self) -> None:
        job = RenderJob(id=uuid.uuid4(), presentation_id=uuid.uuid4())
        assert job.config == RenderConfig()
