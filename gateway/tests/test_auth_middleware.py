"""Tests for JWTAuthMiddleware."""

from __future__ import annotations

import time

import jwt
import pytest
from api_gateway.auth_middleware import _PUBLIC_PATHS, JWTAuthMiddleware
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def _make_app(public_key: str) -> FastAPI:
    app = FastAPI()
    app.add_middleware(JWTAuthMiddleware, public_key=public_key)

    @app.get("/protected")
    def protected(request: Request) -> dict:
        return {"sub": request.state.user.sub, "email": request.state.user.email}

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/api/v1/identity/login")
    def login() -> dict:
        return {"token": "..."}

    @app.get("/api/v1/identity/register")
    def register() -> dict:
        return {"created": True}

    return app


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(public_key_pem) -> TestClient:
    return TestClient(_make_app(public_key_pem), raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# Tests — public paths bypass auth
# ---------------------------------------------------------------------------


def test_health_is_public(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_identity_login_is_public(client):
    resp = client.get("/api/v1/identity/login")
    assert resp.status_code == 200


def test_identity_register_is_public(client):
    resp = client.get("/api/v1/identity/register")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Tests — missing / malformed Authorization header
# ---------------------------------------------------------------------------


def test_missing_auth_header_returns_401(client):
    resp = client.get("/protected")
    assert resp.status_code == 401
    assert "Authorization" in resp.json()["detail"]


def test_non_bearer_header_returns_401(client):
    resp = client.get("/protected", headers={"Authorization": "Basic abc"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests — valid token
# ---------------------------------------------------------------------------


def test_valid_token_passes(client, valid_token):
    resp = client.get("/protected", headers={"Authorization": f"Bearer {valid_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["sub"] == "user-123"
    assert body["email"] == "test@example.com"


# ---------------------------------------------------------------------------
# Tests — expired token
# ---------------------------------------------------------------------------


def test_expired_token_returns_401(client, expired_token):
    resp = client.get("/protected", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Tests — tampered / wrong key
# ---------------------------------------------------------------------------


def test_tampered_signature_returns_401(client, valid_token):
    # Flip the last character of the token
    bad = valid_token[:-1] + ("A" if valid_token[-1] != "A" else "B")
    resp = client.get("/protected", headers={"Authorization": f"Bearer {bad}"})
    assert resp.status_code == 401


def test_wrong_algorithm_token_returns_401(client):
    payload = {"sub": "attacker", "exp": int(time.time()) + 3600}
    hs256_token = jwt.encode(payload, "secret", algorithm="HS256")
    resp = client.get("/protected", headers={"Authorization": f"Bearer {hs256_token}"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests — user context attributes
# ---------------------------------------------------------------------------


def test_roles_in_user_context(public_key_pem, private_key_pem, make_token):
    token = make_token(roles=["admin", "editor"])
    app = _make_app(public_key_pem)

    @app.get("/roles")
    def roles(request: Request) -> dict:
        return {"roles": request.state.user.roles}

    tc = TestClient(app, raise_server_exceptions=True)
    resp = tc.get("/roles", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert set(resp.json()["roles"]) == {"admin", "editor"}


# ---------------------------------------------------------------------------
# Tests — public_paths configuration
# ---------------------------------------------------------------------------


def test_default_public_paths_constant():
    assert "/health" in _PUBLIC_PATHS
    assert "/api/v1/identity/login" in _PUBLIC_PATHS
    assert "/api/v1/identity/register" in _PUBLIC_PATHS


def test_custom_public_paths(public_key_pem):
    app = FastAPI()
    app.add_middleware(
        JWTAuthMiddleware,
        public_key=public_key_pem,
        public_paths=frozenset(["/custom-public"]),
    )

    @app.get("/custom-public")
    def custom() -> dict:
        return {"ok": True}

    @app.get("/protected-still")
    def prot() -> dict:
        return {"ok": True}

    tc = TestClient(app, raise_server_exceptions=True)
    assert tc.get("/custom-public").status_code == 200
    assert tc.get("/protected-still").status_code == 401
