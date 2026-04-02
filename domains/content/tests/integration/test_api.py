"""Integration tests for the content FastAPI router."""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from domains.content.api.router import create_content_router
from domains.content.domain.entities import ContentPlan, SlideContent, SystemPrompt
from domains.content.domain.value_objects import OutlineItem

# ---------------------------------------------------------------------------
# JSON fixtures for mocked LLM
# ---------------------------------------------------------------------------

_OUTLINE_JSON = json.dumps(
    [
        {
            "index": 0,
            "title": "Introduction",
            "key_points": ["What is AI?", "Why it matters"],
            "suggested_layout": "title",
        },
        {
            "index": 1,
            "title": "History",
            "key_points": ["Early days", "Deep learning"],
            "suggested_layout": "content",
        },
    ]
)

_SLIDE_JSON = json.dumps(
    {
        "title": "Introduction",
        "body": "AI is transforming every industry.",
        "speaker_notes": "Start with a question.",
    }
)

_REVISE_JSON = json.dumps(
    {
        "title": "Better Introduction",
        "body": "AI reshapes industries.",
        "speaker_notes": "Open with statistics.",
    }
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_plan_repo(plans: list[ContentPlan] | None = None) -> AsyncMock:
    store: dict[uuid.UUID, ContentPlan] = {p.id: p for p in (plans or [])}
    repo = AsyncMock()

    async def get(id: uuid.UUID) -> ContentPlan | None:
        return store.get(id)

    async def save(plan: ContentPlan) -> None:
        store[plan.id] = plan

    repo.get = AsyncMock(side_effect=get)
    repo.save = AsyncMock(side_effect=save)
    return repo


def _make_content_repo(contents: list[SlideContent] | None = None) -> AsyncMock:
    store: dict[uuid.UUID, SlideContent] = {sc.id: sc for sc in (contents or [])}
    repo = AsyncMock()

    async def get(id: uuid.UUID) -> SlideContent | None:
        return store.get(id)

    async def save(sc: SlideContent) -> None:
        store[sc.id] = sc

    repo.get = AsyncMock(side_effect=get)
    repo.save = AsyncMock(side_effect=save)
    return repo


def _make_prompt_repo(prompts: list[SystemPrompt] | None = None) -> AsyncMock:
    store: dict[uuid.UUID, SystemPrompt] = {sp.id: sp for sp in (prompts or [])}
    repo = AsyncMock()

    async def get(id: uuid.UUID) -> SystemPrompt | None:
        return store.get(id)

    async def save(sp: SystemPrompt) -> None:
        store[sp.id] = sp

    async def list_all() -> list[SystemPrompt]:
        return list(store.values())

    repo.get = AsyncMock(side_effect=get)
    repo.save = AsyncMock(side_effect=save)
    repo.list_all = AsyncMock(side_effect=list_all)
    return repo


def _make_llm(return_value: str = _OUTLINE_JSON) -> AsyncMock:
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=return_value)
    return llm


def create_test_app(
    plan_repo: AsyncMock | None = None,
    content_repo: AsyncMock | None = None,
    prompt_repo: AsyncMock | None = None,
    llm: AsyncMock | None = None,
) -> FastAPI:
    app = FastAPI()
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock()
    router = create_content_router(
        plan_repo=plan_repo or _make_plan_repo(),
        content_repo=content_repo or _make_content_repo(),
        prompt_repo=prompt_repo or _make_prompt_repo(),
        event_bus=event_bus,
        llm=llm or _make_llm(),
    )
    app.include_router(router)
    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGenerateOutline:
    async def test_returns_201(self) -> None:
        app = create_test_app(llm=_make_llm(_OUTLINE_JSON))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/content/outline",
                json={"topic": "Artificial Intelligence", "num_slides": 2},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["topic"] == "Artificial Intelligence"
        assert len(data["outline"]) == 2

    async def test_empty_topic_returns_422(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post("/content/outline", json={"topic": ""})
        assert resp.status_code == 422

    async def test_invalid_num_slides_returns_422(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post("/content/outline", json={"topic": "AI", "num_slides": 0})
        assert resp.status_code == 422

    async def test_outline_items_structure(self) -> None:
        app = create_test_app(llm=_make_llm(_OUTLINE_JSON))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/content/outline",
                json={"topic": "AI", "num_slides": 2},
            )
        data = resp.json()
        item = data["outline"][0]
        assert "index" in item
        assert "title" in item
        assert "key_points" in item
        assert "suggested_layout" in item


class TestGenerateSlide:
    async def test_returns_201(self) -> None:
        plan = ContentPlan(id=uuid.uuid4(), presentation_id=uuid.uuid4(), topic="AI")
        plan.add_item(
            OutlineItem(index=0, title="Introduction", key_points=("p1",), suggested_layout="title")
        )
        plan_repo = _make_plan_repo([plan])
        app = create_test_app(plan_repo=plan_repo, llm=_make_llm(_SLIDE_JSON))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(f"/content/slides/{plan.id}/0")
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Introduction"
        assert data["slide_index"] == 0

    async def test_missing_plan_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(f"/content/slides/{uuid.uuid4()}/0")
        assert resp.status_code == 404

    async def test_missing_slide_index_returns_404(self) -> None:
        plan = ContentPlan(id=uuid.uuid4(), presentation_id=uuid.uuid4(), topic="AI")
        plan.add_item(OutlineItem(index=0, title="Intro", key_points=(), suggested_layout="title"))
        plan_repo = _make_plan_repo([plan])
        app = create_test_app(plan_repo=plan_repo, llm=_make_llm(_SLIDE_JSON))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(f"/content/slides/{plan.id}/99")
        assert resp.status_code == 404


class TestReviseContent:
    async def test_returns_200(self) -> None:
        sc = SlideContent(
            id=uuid.uuid4(),
            plan_id=uuid.uuid4(),
            slide_index=0,
            title="Intro",
            body="Old body",
            speaker_notes="Old notes",
        )
        content_repo = _make_content_repo([sc])
        app = create_test_app(content_repo=content_repo, llm=_make_llm(_REVISE_JSON))
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                f"/content/revise/{sc.id}",
                json={"feedback": "Make it more engaging"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Better Introduction"

    async def test_missing_content_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                f"/content/revise/{uuid.uuid4()}",
                json={"feedback": "Feedback"},
            )
        assert resp.status_code == 404

    async def test_empty_feedback_returns_422(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                f"/content/revise/{uuid.uuid4()}",
                json={"feedback": ""},
            )
        assert resp.status_code == 422


class TestGetPlan:
    async def test_get_existing_plan(self) -> None:
        plan = ContentPlan(id=uuid.uuid4(), presentation_id=uuid.uuid4(), topic="AI")
        plan_repo = _make_plan_repo([plan])
        app = create_test_app(plan_repo=plan_repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get(f"/content/plans/{plan.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == str(plan.id)

    async def test_missing_plan_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get(f"/content/plans/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestSystemPrompts:
    async def test_list_empty(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/content/prompts")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_with_items(self) -> None:
        sp = SystemPrompt(
            id=uuid.uuid4(),
            name="outline_generator",
            prompt_text="Generate {topic}",
            variables=["topic"],
        )
        prompt_repo = _make_prompt_repo([sp])
        app = create_test_app(prompt_repo=prompt_repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.get("/content/prompts")
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["name"] == "outline_generator"

    async def test_create_prompt(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/content/prompts",
                json={
                    "name": "slide_writer",
                    "prompt_text": "Write slide for {topic}",
                    "variables": ["topic"],
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "slide_writer"
        assert data["variables"] == ["topic"]

    async def test_create_prompt_empty_name_returns_422(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.post(
                "/content/prompts",
                json={"name": "", "prompt_text": "text"},
            )
        assert resp.status_code == 422

    async def test_update_prompt(self) -> None:
        sp = SystemPrompt(id=uuid.uuid4(), name="test", prompt_text="Old text", variables=[])
        prompt_repo = _make_prompt_repo([sp])
        app = create_test_app(prompt_repo=prompt_repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.put(
                f"/content/prompts/{sp.id}",
                json={"prompt_text": "New text"},
            )
        assert resp.status_code == 200
        assert resp.json()["prompt_text"] == "New text"

    async def test_update_missing_prompt_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            resp = await c.put(
                f"/content/prompts/{uuid.uuid4()}",
                json={"prompt_text": "New"},
            )
        assert resp.status_code == 404
