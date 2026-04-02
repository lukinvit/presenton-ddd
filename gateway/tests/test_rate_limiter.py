"""Tests for RateLimiterMiddleware."""

from __future__ import annotations

import time

from api_gateway.rate_limiter import RateLimiterMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------


def _make_app(requests_per_minute: int) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RateLimiterMiddleware, requests_per_minute=requests_per_minute)

    @app.get("/ping")
    def ping() -> dict:
        return {"pong": True}

    return app


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_requests_under_limit_pass():
    """All requests within the limit should succeed."""
    app = _make_app(requests_per_minute=5)
    client = TestClient(app, raise_server_exceptions=True)
    for _ in range(5):
        resp = client.get("/ping")
        assert resp.status_code == 200


def test_request_over_limit_returns_429():
    """The request immediately exceeding the limit should return 429."""
    app = _make_app(requests_per_minute=3)
    client = TestClient(app, raise_server_exceptions=True)
    for _ in range(3):
        client.get("/ping")
    resp = client.get("/ping")
    assert resp.status_code == 429
    body = resp.json()
    assert body["detail"] == "Too Many Requests"
    assert body["retry_after"] == 60


def test_retry_after_header_present():
    app = _make_app(requests_per_minute=1)
    client = TestClient(app, raise_server_exceptions=True)
    client.get("/ping")  # consume limit
    resp = client.get("/ping")
    assert resp.status_code == 429
    assert resp.headers["Retry-After"] == "60"


def test_different_ips_have_separate_buckets():
    """Two clients with different IPs share no rate-limit state."""
    app = _make_app(requests_per_minute=2)
    client_a = TestClient(app, raise_server_exceptions=True)
    client_b = TestClient(app, raise_server_exceptions=True)

    # Exhaust client_a quota
    client_a.get("/ping", headers={"X-Forwarded-For": "10.0.0.1"})
    client_a.get("/ping", headers={"X-Forwarded-For": "10.0.0.1"})
    assert client_a.get("/ping", headers={"X-Forwarded-For": "10.0.0.1"}).status_code == 429

    # client_b (different IP) should still be allowed
    assert client_b.get("/ping", headers={"X-Forwarded-For": "10.0.0.2"}).status_code == 200


def test_sliding_window_resets_after_a_minute():
    """After the 60-second window expires the IP's bucket empties."""
    from api_gateway.rate_limiter import RateLimiterMiddleware as RL

    limiter = RL.__new__(RL)  # bypass __init__ to control state
    limiter._window = {}

    from collections import defaultdict, deque

    limiter._window = defaultdict(deque)
    limiter.requests_per_minute = 1

    ip = "192.168.1.1"
    # Simulate one old request (61 seconds ago — outside window)
    limiter._window[ip].append(time.monotonic() - 61)

    assert limiter._is_allowed(ip) is True, "Old request outside window should not count"


def test_limit_exact_boundary():
    """Exactly `requests_per_minute` requests are allowed, the next is denied."""
    limit = 10
    app = _make_app(requests_per_minute=limit)
    client = TestClient(app, raise_server_exceptions=True)
    for i in range(limit):
        r = client.get("/ping")
        assert r.status_code == 200, f"Request {i + 1} should pass"
    # One more should fail
    assert client.get("/ping").status_code == 429


def test_x_forwarded_for_header_used_for_ip():
    """The middleware should honour X-Forwarded-For for IP extraction."""
    app = _make_app(requests_per_minute=1)
    client = TestClient(app, raise_server_exceptions=True)
    # First request — under limit
    r1 = client.get("/ping", headers={"X-Forwarded-For": "203.0.113.5"})
    assert r1.status_code == 200
    # Second request same IP — over limit
    r2 = client.get("/ping", headers={"X-Forwarded-For": "203.0.113.5"})
    assert r2.status_code == 429
