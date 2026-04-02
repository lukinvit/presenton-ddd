"""Unit tests for presentation domain entities and value objects."""

from __future__ import annotations

import uuid

from domains.presentation.domain.entities import Presentation, Slide, Template
from domains.presentation.domain.value_objects import ElementType, PresentationStatus, SlideElement


class TestPresentationStatus:
    def test_all_statuses_exist(self) -> None:
        assert PresentationStatus.DRAFT.value == "draft"
        assert PresentationStatus.GENERATING.value == "generating"
        assert PresentationStatus.REVIEW.value == "review"
        assert PresentationStatus.FINAL.value == "final"


class TestElementType:
    def test_all_types_exist(self) -> None:
        assert ElementType.TEXT.value == "text"
        assert ElementType.IMAGE.value == "image"
        assert ElementType.INFOGRAPHIC.value == "infographic"
        assert ElementType.ICON.value == "icon"
        assert ElementType.CHART.value == "chart"


class TestSlideElement:
    def test_create_element(self) -> None:
        el = SlideElement(
            type=ElementType.TEXT,
            content="Hello world",
            position={"x": 0, "y": 0, "width": 100, "height": 50},
            style={"font_size": 24},
        )
        assert el.content == "Hello world"
        assert el.type == ElementType.TEXT

    def test_element_equality(self) -> None:
        el1 = SlideElement(
            type=ElementType.TEXT,
            content="Same",
            position={"x": 0},
            style={},
        )
        el2 = SlideElement(
            type=ElementType.TEXT,
            content="Same",
            position={"x": 0},
            style={},
        )
        assert el1 == el2

    def test_element_inequality_on_content(self) -> None:
        el1 = SlideElement(type=ElementType.TEXT, content="A", position={}, style={})
        el2 = SlideElement(type=ElementType.TEXT, content="B", position={}, style={})
        assert el1 != el2


class TestSlide:
    def test_create_slide(self) -> None:
        slide = Slide(
            id=uuid.uuid4(),
            presentation_id=uuid.uuid4(),
            title="Intro",
            layout_type="title",
        )
        assert slide.title == "Intro"
        assert slide.elements == []

    def test_add_element(self) -> None:
        slide = Slide(id=uuid.uuid4(), presentation_id=uuid.uuid4(), title="Slide")
        el = SlideElement(type=ElementType.TEXT, content="text", position={}, style={})
        slide.add_element(el)
        assert len(slide.elements) == 1

    def test_replace_elements(self) -> None:
        slide = Slide(id=uuid.uuid4(), presentation_id=uuid.uuid4(), title="Slide")
        el1 = SlideElement(type=ElementType.TEXT, content="old", position={}, style={})
        slide.add_element(el1)
        el2 = SlideElement(type=ElementType.IMAGE, content="url", position={}, style={})
        slide.replace_elements([el2])
        assert len(slide.elements) == 1
        assert slide.elements[0].type == ElementType.IMAGE


class TestPresentation:
    def _make_presentation(self) -> Presentation:
        return Presentation(id=uuid.uuid4(), title="Test", description="Desc")

    def test_create_presentation(self) -> None:
        p = self._make_presentation()
        assert p.title == "Test"
        assert p.status == PresentationStatus.DRAFT
        assert p.slides == []

    def test_add_slide_increments_index(self) -> None:
        p = self._make_presentation()
        s1 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S1")
        s2 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S2")
        p.add_slide(s1)
        p.add_slide(s2)
        assert s1.index == 0
        assert s2.index == 1

    def test_insert_slide_reindexes(self) -> None:
        p = self._make_presentation()
        s1 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S1")
        s2 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S2")
        p.add_slide(s1)
        p.add_slide(s2)
        # insert before s1
        s0 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S0")
        p.insert_slide(s0, 0)
        assert p.slides[0].title == "S0"
        assert p.slides[0].index == 0
        assert p.slides[1].index == 1
        assert p.slides[2].index == 2

    def test_remove_slide(self) -> None:
        p = self._make_presentation()
        s1 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S1")
        s2 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S2")
        p.add_slide(s1)
        p.add_slide(s2)
        p.remove_slide(s1.id)
        assert len(p.slides) == 1
        assert p.slides[0].id == s2.id
        assert p.slides[0].index == 0

    def test_remove_nonexistent_slide_is_noop(self) -> None:
        p = self._make_presentation()
        p.remove_slide(uuid.uuid4())
        assert p.slides == []

    def test_get_slide(self) -> None:
        p = self._make_presentation()
        s = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S")
        p.add_slide(s)
        assert p.get_slide(s.id) is s
        assert p.get_slide(uuid.uuid4()) is None

    def test_reorder_slides(self) -> None:
        p = self._make_presentation()
        s1 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S1")
        s2 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S2")
        s3 = Slide(id=uuid.uuid4(), presentation_id=p.id, title="S3")
        p.add_slide(s1)
        p.add_slide(s2)
        p.add_slide(s3)
        p.reorder_slides([s3.id, s1.id, s2.id])
        assert p.slides[0].title == "S3"
        assert p.slides[1].title == "S1"
        assert p.slides[2].title == "S2"
        assert all(s.index == i for i, s in enumerate(p.slides))

    def test_update_status(self) -> None:
        p = self._make_presentation()
        p.update_status(PresentationStatus.REVIEW)
        assert p.status == PresentationStatus.REVIEW

    def test_update_title(self) -> None:
        p = self._make_presentation()
        p.update_title("New Title")
        assert p.title == "New Title"


class TestTemplate:
    def test_create_template(self) -> None:
        t = Template(
            id=uuid.uuid4(),
            name="Default",
            description="Simple template",
            html_template="<html></html>",
            css="body {}",
            is_builtin=True,
        )
        assert t.name == "Default"
        assert t.is_builtin is True
