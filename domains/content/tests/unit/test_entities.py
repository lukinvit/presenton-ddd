"""Unit tests for content domain entities and value objects."""

from __future__ import annotations

import uuid

from domains.content.domain.entities import ContentPlan, SlideContent, SystemPrompt
from domains.content.domain.value_objects import OutlineItem, PromptTemplate


class TestOutlineItem:
    def test_equality(self) -> None:
        a = OutlineItem(index=0, title="Intro", key_points=("p1",), suggested_layout="title")
        b = OutlineItem(index=0, title="Intro", key_points=("p1",), suggested_layout="title")
        assert a == b

    def test_inequality_different_index(self) -> None:
        a = OutlineItem(index=0, title="Intro", key_points=(), suggested_layout="title")
        b = OutlineItem(index=1, title="Intro", key_points=(), suggested_layout="title")
        assert a != b

    def test_hashable(self) -> None:
        item = OutlineItem(index=0, title="Intro", key_points=("p1",), suggested_layout="title")
        assert hash(item) == hash(item)


class TestPromptTemplate:
    def test_render_replaces_variables(self) -> None:
        t = PromptTemplate(
            template="Write about {topic} in {tone} tone.",
            variables={"topic": "AI", "tone": "formal"},
        )
        assert t.render() == "Write about AI in formal tone."

    def test_render_missing_variable_keeps_placeholder(self) -> None:
        t = PromptTemplate(
            template="Write about {topic}.",
            variables={},
        )
        assert t.render() == "Write about {topic}."

    def test_equality(self) -> None:
        a = PromptTemplate(template="Hello {name}", variables={"name": "World"})
        b = PromptTemplate(template="Hello {name}", variables={"name": "World"})
        assert a == b

    def test_hashable(self) -> None:
        t = PromptTemplate(template="Hello", variables={})
        s = {t}
        assert t in s


class TestContentPlan:
    def test_add_item(self) -> None:
        plan = ContentPlan(id=uuid.uuid4(), presentation_id=uuid.uuid4(), topic="AI")
        item = OutlineItem(index=0, title="Intro", key_points=("p1",), suggested_layout="title")
        plan.add_item(item)
        assert len(plan.outline) == 1
        assert plan.outline[0] == item

    def test_replace_outline(self) -> None:
        plan = ContentPlan(id=uuid.uuid4(), presentation_id=uuid.uuid4(), topic="AI")
        items = [
            OutlineItem(index=i, title=f"Slide {i}", key_points=(), suggested_layout="content")
            for i in range(3)
        ]
        plan.replace_outline(items)
        assert len(plan.outline) == 3


class TestSlideContent:
    def test_creation(self) -> None:
        sc = SlideContent(
            id=uuid.uuid4(),
            plan_id=uuid.uuid4(),
            slide_index=0,
            title="Intro",
            body="Welcome to the presentation",
            speaker_notes="Remember to greet the audience.",
        )
        assert sc.title == "Intro"
        assert sc.slide_index == 0


class TestSystemPrompt:
    def test_update_text(self) -> None:
        sp = SystemPrompt(id=uuid.uuid4(), name="test", prompt_text="Old text")
        old_ts = sp.updated_at
        sp.update_text("New text")
        assert sp.prompt_text == "New text"
        assert sp.updated_at >= old_ts

    def test_update_variables(self) -> None:
        sp = SystemPrompt(id=uuid.uuid4(), name="test", prompt_text="Text", variables=["a"])
        sp.update_variables(["b", "c"])
        assert sp.variables == ["b", "c"]
