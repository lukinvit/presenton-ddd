"""Integration tests for the style domain FastAPI router."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from domains.style.api.router import create_style_router
from domains.style.domain.entities import StyleProfile
from domains.style.domain.value_objects import ColorPalette, LayoutRules, Spacing, Typography

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_full_profile(name: str = "Test Profile") -> StyleProfile:
    profile = StyleProfile(id=uuid.uuid4(), name=name, source="custom")
    profile.update_colors(
        ColorPalette(
            primary="#1A1A1A",
            secondary="#555555",
            accent=("#0066CC",),
            background="#FFFFFF",
            text="#1A1A1A",
        )
    )
    profile.update_typography(
        Typography.from_sizes_dict(
            heading_font="Inter",
            body_font="Inter",
            sizes={"h1": "36px", "h2": "28px", "h3": "22px", "body": "16px"},
        )
    )
    profile.update_layout(
        LayoutRules(
            margin="40px",
            padding="24px",
            alignment_grid=12,
            max_content_width="1200px",
        )
    )
    profile.update_spacing(Spacing(line_height="1.5", paragraph_gap="20px", element_gap="16px"))
    return profile


def _make_profile_repo(profiles: list[StyleProfile] | None = None) -> AsyncMock:
    store: dict[uuid.UUID, StyleProfile] = {p.id: p for p in (profiles or [])}
    repo = AsyncMock()

    async def get(id: uuid.UUID) -> StyleProfile | None:
        return store.get(id)

    async def save(profile: StyleProfile) -> None:
        store[profile.id] = profile

    async def delete(id: uuid.UUID) -> None:
        store.pop(id, None)

    async def list_all(limit: int = 50, offset: int = 0) -> list[StyleProfile]:
        items = list(store.values())
        return items[offset : offset + limit]

    repo.get = AsyncMock(side_effect=get)
    repo.save = AsyncMock(side_effect=save)
    repo.delete = AsyncMock(side_effect=delete)
    repo.list_all = AsyncMock(side_effect=list_all)
    return repo


def _make_preset_repo() -> AsyncMock:
    from domains.style.domain.entities import StylePreset

    store: dict[uuid.UUID, StylePreset] = {}
    repo = AsyncMock()

    async def get(id: uuid.UUID):
        return store.get(id)

    async def get_by_name(name: str):
        return next((p for p in store.values() if p.name == name), None)

    async def save(preset: StylePreset) -> None:
        store[preset.id] = preset

    async def list_all(limit: int = 100, offset: int = 0):
        items = list(store.values())
        return items[offset : offset + limit]

    repo.get = AsyncMock(side_effect=get)
    repo.get_by_name = AsyncMock(side_effect=get_by_name)
    repo.save = AsyncMock(side_effect=save)
    repo.list_all = AsyncMock(side_effect=list_all)
    return repo


def create_test_app(
    profile_repo: AsyncMock | None = None,
    preset_repo: AsyncMock | None = None,
) -> FastAPI:
    app = FastAPI()
    profile_repo = profile_repo or _make_profile_repo()
    preset_repo = preset_repo or _make_preset_repo()
    event_bus = AsyncMock()
    event_bus.publish = AsyncMock()
    router = create_style_router(
        profile_repo=profile_repo,
        preset_repo=preset_repo,
        event_bus=event_bus,
    )
    app.include_router(router)
    return app


# ---------------------------------------------------------------------------
# GET /styles/{id}
# ---------------------------------------------------------------------------


class TestGetStyleProfile:
    async def test_get_existing_profile(self) -> None:
        p = _make_full_profile()
        repo = _make_profile_repo([p])
        app = create_test_app(profile_repo=repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/styles/{p.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(p.id)
        assert data["colors"]["primary"] == "#1A1A1A"

    async def test_get_missing_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/styles/{uuid.uuid4()}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /styles/extract-from-file
# ---------------------------------------------------------------------------


class TestExtractFromFile:
    async def test_extract_valid_pptx(self, tmp_path) -> None:
        dummy = tmp_path / "deck.pptx"
        dummy.write_bytes(b"dummy")

        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/styles/extract-from-file",
                json={"file_path": str(dummy), "name": "My Deck"},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source"] == "file"
        assert data["name"] == "My Deck"

    async def test_extract_missing_file_returns_400(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/styles/extract-from-file",
                json={"file_path": "/no/such/file.pptx", "name": "Bad"},
            )
        assert resp.status_code == 400

    async def test_extract_empty_name_returns_422(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/styles/extract-from-file",
                json={"file_path": "/some/file.pptx", "name": ""},
            )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /styles/extract-from-url
# ---------------------------------------------------------------------------


class TestExtractFromURL:
    async def test_extract_from_url_returns_201(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/styles/extract-from-url",
                json={"url": "https://example.com", "name": "Example"},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["source"] == "url"
        assert data["name"] == "Example"


# ---------------------------------------------------------------------------
# POST /styles/{id}/apply/{presentation_id}
# ---------------------------------------------------------------------------


class TestApplyStyle:
    async def test_apply_existing_profile(self) -> None:
        p = _make_full_profile()
        repo = _make_profile_repo([p])
        app = create_test_app(profile_repo=repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(f"/styles/{p.id}/apply/{uuid.uuid4()}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    async def test_apply_missing_profile_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(f"/styles/{uuid.uuid4()}/apply/{uuid.uuid4()}")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /styles/{id}/validate
# ---------------------------------------------------------------------------


class TestValidateStyle:
    async def test_validate_matching_colors(self) -> None:
        p = _make_full_profile()
        repo = _make_profile_repo([p])
        app = create_test_app(profile_repo=repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/styles/{p.id}/validate",
                json={"colors": ["#1A1A1A", "#FFFFFF"], "fonts": ["inter"], "bg_color": "#FFFFFF"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["profile_id"] == str(p.id)
        cc = next(c for c in data["criteria"] if c["criterion"] == "color_consistency")
        assert cc["passed"] is True

    async def test_validate_unknown_color_fails(self) -> None:
        p = _make_full_profile()
        repo = _make_profile_repo([p])
        app = create_test_app(profile_repo=repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/styles/{p.id}/validate",
                json={"colors": ["#DEADBE"], "fonts": [], "bg_color": ""},
            )
        assert resp.status_code == 200
        data = resp.json()
        cc = next(c for c in data["criteria"] if c["criterion"] == "color_consistency")
        assert cc["passed"] is False

    async def test_validate_missing_profile_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/styles/{uuid.uuid4()}/validate",
                json={"colors": [], "fonts": [], "bg_color": ""},
            )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /styles/{id}/css
# ---------------------------------------------------------------------------


class TestGetCSS:
    async def test_get_css_returns_root_block(self) -> None:
        p = _make_full_profile()
        repo = _make_profile_repo([p])
        app = create_test_app(profile_repo=repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/styles/{p.id}/css")
        assert resp.status_code == 200
        data = resp.json()
        assert ":root {" in data["css"]
        assert "--color-primary" in data["css"]

    async def test_get_css_missing_profile_returns_404(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/styles/{uuid.uuid4()}/css")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /styles/{id}/tailwind
# ---------------------------------------------------------------------------


class TestGetTailwind:
    async def test_get_tailwind_returns_theme(self) -> None:
        p = _make_full_profile()
        repo = _make_profile_repo([p])
        app = create_test_app(profile_repo=repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"/styles/{p.id}/tailwind")
        assert resp.status_code == 200
        data = resp.json()
        assert "theme" in data
        assert "extend" in data["theme"]


# ---------------------------------------------------------------------------
# GET /styles/presets
# ---------------------------------------------------------------------------


class TestListPresets:
    async def test_list_includes_builtins(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/styles/presets")
        assert resp.status_code == 200
        data = resp.json()
        names = {p["name"] for p in data}
        assert "minimal-light" in names
        assert "corporate-blue" in names
        assert len(data) >= 5


# ---------------------------------------------------------------------------
# POST /styles/presets
# ---------------------------------------------------------------------------


class TestCreatePreset:
    async def test_create_preset_from_existing_profile(self) -> None:
        p = _make_full_profile()
        profile_repo = _make_profile_repo([p])
        preset_repo = _make_preset_repo()
        app = create_test_app(profile_repo=profile_repo, preset_repo=preset_repo)
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/styles/presets",
                json={
                    "name": "My Preset",
                    "description": "Cool preset",
                    "profile_id": str(p.id),
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Preset"
        assert data["is_builtin"] is False

    async def test_create_preset_missing_profile_returns_400(self) -> None:
        app = create_test_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/styles/presets",
                json={
                    "name": "X",
                    "description": "",
                    "profile_id": str(uuid.uuid4()),
                },
            )
        assert resp.status_code == 400
