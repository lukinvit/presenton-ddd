from unittest.mock import AsyncMock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from domains.identity.api.router import create_identity_router
from domains.identity.domain.services import TokenService


def create_test_app() -> FastAPI:
    app = FastAPI()
    user_repo = AsyncMock()
    user_repo.get_by_email = AsyncMock(return_value=None)
    user_repo.save = AsyncMock()
    event_bus = AsyncMock()
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    ).decode()
    public_pem = (
        private_key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    token_service = TokenService(private_key=private_pem, public_key=public_pem)
    router = create_identity_router(user_repo, event_bus, token_service)
    app.include_router(router)
    return app


class TestIdentityAPI:
    @pytest.mark.asyncio
    async def test_register_endpoint(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/register", json={"email": "new@example.com", "password": "secret123"}
            )
            assert resp.status_code == 201
            data = resp.json()
            assert "access_token" in data
            assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_register_invalid_email_returns_422(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/register", json={"email": "", "password": "secret123"})
            assert resp.status_code == 422
