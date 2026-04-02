"""Reverse proxy — routes /api/v1/{domain}/* to the corresponding domain service."""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Request, Response

router = APIRouter()

# Domain prefix -> upstream base URL
UPSTREAMS: dict[str, str] = {
    "presentations": os.getenv("PRESENTATION_URL", "http://presentation:8010"),
    "styles": os.getenv("STYLE_URL", "http://style:8020"),
    "content": os.getenv("CONTENT_URL", "http://content:8030"),
    "rendering": os.getenv("RENDERING_URL", "http://rendering:8040"),
    "media": os.getenv("MEDIA_URL", "http://media:8050"),
    "agents": os.getenv("AGENT_URL", "http://agent:8060"),
    "auth": os.getenv("AUTH_URL", "http://auth:8070"),
    "identity": os.getenv("IDENTITY_URL", "http://identity:8080"),
    "web": os.getenv("WEB_ACCESS_URL", "http://web_access:8090"),
    "export": os.getenv("EXPORT_URL", "http://export:8100"),
}

# Identity domain registers routes at /api/v1/* (register, login)
# so we also need a direct proxy for those top-level auth routes
AUTH_ROUTES = {"/api/v1/register", "/api/v1/login", "/api/v1/refresh"}


@router.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy(request: Request, path: str) -> Response:
    """Proxy requests to domain services based on URL prefix."""
    # Check if it's a top-level auth route
    full_path = f"/api/v1/{path}"
    if full_path in AUTH_ROUTES:
        upstream = UPSTREAMS["identity"]
        target_url = f"{upstream}{full_path}"
    else:
        # Extract domain prefix from path
        parts = path.split("/", 1)
        prefix = parts[0]
        remainder = parts[1] if len(parts) > 1 else ""

        upstream = UPSTREAMS.get(prefix)
        if upstream is None:
            return Response(
                content=f'{{"detail":"Unknown domain: {prefix}"}}',
                status_code=404,
                media_type="application/json",
            )
        target_url = f"{upstream}/api/v1/{remainder}" if remainder else f"{upstream}/api/v1"

    # Forward the request
    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
            params=dict(request.query_params),
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=dict(resp.headers),
        media_type=resp.headers.get("content-type"),
    )
