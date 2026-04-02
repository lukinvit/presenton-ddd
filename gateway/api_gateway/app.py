"""FastAPI gateway application factory."""

from __future__ import annotations

import os

from api_gateway.auth_middleware import JWTAuthMiddleware
from api_gateway.health import router as health_router
from api_gateway.rate_limiter import RateLimiterMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app(
    public_key: str | None = None,
    requests_per_minute: int = 60,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    """Create and configure the FastAPI gateway application.

    Args:
        public_key: RSA public key PEM string for JWT validation.
                    Falls back to the JWT_PUBLIC_KEY environment variable.
        requests_per_minute: Per-IP rate limit.
        cors_origins: Allowed CORS origins.
    """
    resolved_public_key = public_key or os.getenv("JWT_PUBLIC_KEY", "")
    allowed_origins = cors_origins or ["*"]

    app = FastAPI(
        title="Presenton Gateway",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS — must be added before auth so preflight OPTIONS passes through
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.add_middleware(RateLimiterMiddleware, requests_per_minute=requests_per_minute)

    # JWT auth (only when a public key is configured)
    if resolved_public_key:
        app.add_middleware(JWTAuthMiddleware, public_key=resolved_public_key)

    # Routers
    app.include_router(health_router)

    from api_gateway.proxy import router as proxy_router
    app.include_router(proxy_router)

    return app


app = create_app()
