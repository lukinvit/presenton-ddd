from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from domains.auth.api.router import create_auth_router


def create_test_app() -> FastAPI:
    app = FastAPI()
    oauth_adapter = AsyncMock()
    oauth_adapter.get_authorize_url.return_value = (
        "https://console.anthropic.com/oauth/authorize?state=test",
        "test_state",
        "test_verifier",
    )
    state_repo = AsyncMock()
    connection_repo = AsyncMock()
    encryption_service = MagicMock()
    event_bus = AsyncMock()
    router = create_auth_router(
        oauth_adapters={"anthropic": oauth_adapter},
        state_repo=state_repo,
        connection_repo=connection_repo,
        encryption_service=encryption_service,
        event_bus=event_bus,
    )
    app.include_router(router)
    return app


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_initiate_oauth(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/connect",
                json={
                    "provider": "anthropic",
                    "redirect_uri": "http://localhost:5000/api/v1/auth/callback",
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "authorize_url" in data
            assert "anthropic.com" in data["authorize_url"]

    @pytest.mark.asyncio
    async def test_connect_unknown_provider_returns_400(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/connect",
                json={"provider": "nonexistent", "redirect_uri": "http://localhost:5000"},
            )
            assert resp.status_code == 400
