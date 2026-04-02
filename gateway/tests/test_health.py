"""Tests for the aggregated health endpoint."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from api_gateway.app import create_app
from api_gateway.health import DOMAIN_HEALTH_URLS, _check_domain
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Unit tests for _check_domain helper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_check_domain_ok():
    """Domain returning 200 is reported as ok."""
    mock_resp = AsyncMock()
    mock_resp.status_code = 200

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    result = await _check_domain(mock_client, "presentation", "http://presentation:8010")
    assert result["status"] == "ok"
    assert result["domain"] == "presentation"


@pytest.mark.asyncio
async def test_check_domain_degraded():
    """Domain returning non-200 is reported as degraded."""
    mock_resp = AsyncMock()
    mock_resp.status_code = 503

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_resp)

    result = await _check_domain(mock_client, "style", "http://style:8020")
    assert result["status"] == "degraded"
    assert result["http_status"] == 503


@pytest.mark.asyncio
async def test_check_domain_unreachable():
    """Connection errors map to unreachable."""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=ConnectionRefusedError("refused"))

    result = await _check_domain(mock_client, "content", "http://content:8030")
    assert result["status"] == "unreachable"
    assert "error" in result


# ---------------------------------------------------------------------------
# Integration tests via TestClient (mocked httpx)
# ---------------------------------------------------------------------------


def _make_ok_response():
    resp = AsyncMock()
    resp.status_code = 200
    return resp


def _patched_check(status: str):
    async def _fn(client, name, base_url):
        return {"domain": name, "status": status}

    return _fn


@pytest.fixture
def app_client():
    app = create_app(public_key="", requests_per_minute=9999)
    return TestClient(app, raise_server_exceptions=True)


def test_health_endpoint_all_ok(app_client):
    with patch("api_gateway.health._check_domain", side_effect=_patched_check("ok")):
        resp = app_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert len(body["domains"]) == len(DOMAIN_HEALTH_URLS)


def test_health_endpoint_one_degraded(app_client):
    call_count = [0]

    async def _mixed_check(client, name, base_url):
        call_count[0] += 1
        if name == "rendering":
            return {"domain": name, "status": "degraded"}
        return {"domain": name, "status": "ok"}

    with patch("api_gateway.health._check_domain", side_effect=_mixed_check):
        resp = app_client.get("/health")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "degraded"
    degraded = [d for d in body["domains"] if d["status"] == "degraded"]
    assert any(d["domain"] == "rendering" for d in degraded)


def test_health_endpoint_domain_count(app_client):
    with patch("api_gateway.health._check_domain", side_effect=_patched_check("ok")):
        resp = app_client.get("/health")
    assert len(resp.json()["domains"]) == 10
