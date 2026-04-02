"""Aggregated health endpoint."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from fastapi import APIRouter

router = APIRouter()

# Map of domain name -> base URL for health checks
DOMAIN_HEALTH_URLS: dict[str, str] = {
    "presentation": "http://presentation:8010",
    "style": "http://style:8020",
    "content": "http://content:8030",
    "rendering": "http://rendering:8040",
    "media": "http://media:8050",
    "agent": "http://agent:8060",
    "auth": "http://auth:8070",
    "identity": "http://identity:8080",
    "web_access": "http://web_access:8090",
    "export": "http://export:8100",
}


async def _check_domain(client: httpx.AsyncClient, name: str, base_url: str) -> dict[str, Any]:
    try:
        resp = await client.get(f"{base_url}/health", timeout=3.0)
        if resp.status_code == 200:
            return {"domain": name, "status": "ok", "http_status": resp.status_code}
        return {"domain": name, "status": "degraded", "http_status": resp.status_code}
    except Exception as exc:
        return {"domain": name, "status": "unreachable", "error": str(exc)}


@router.get("/health")
async def health() -> dict[str, Any]:
    """Check all domain health endpoints and return an aggregated result."""
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[_check_domain(client, name, url) for name, url in DOMAIN_HEALTH_URLS.items()]
        )

    statuses = [r["status"] for r in results]
    overall = "ok" if all(s == "ok" for s in statuses) else "degraded"
    return {
        "status": overall,
        "domains": list(results),
    }
