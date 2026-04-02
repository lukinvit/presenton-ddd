"""Start all domains in a single Python process (Electron embedded mode).

Key differences from the Docker / microservices deployment:
  - Uses InMemoryEventBus instead of Redis.
  - Uses SQLite instead of PostgreSQL.
  - All domain routers are mounted into a single FastAPI application.
  - No inter-process MCP TCP transport — MCP servers are called in-process.

Environment variables consumed:
  PRESENTON_DB_PATH   — absolute path to the SQLite database file.
  PRESENTON_PORT      — port the embedded server listens on (default: 8000).
  PRESENTON_ENV       — must be "electron" (guards against accidental use elsewhere).
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ─── Embedded infrastructure ──────────────────────────────────────────────────

from embedded_bus import shared_event_bus
from embedded_db import get_shared_engine

# ─── Domain router factories ───────────────────────────────────────────────────
# Each domain exposes a `create_<domain>_router(...)` factory that accepts
# shared dependencies (engine, event_bus) instead of reading them from env.

from domains.identity.api.router import create_identity_router
from domains.auth.api.router import create_auth_router
from domains.presentation.api.router import create_presentation_router
from domains.content.api.router import create_content_router
from domains.style.api.router import create_style_router
from domains.media.api.router import create_media_router
from domains.export.api.router import create_export_router
from domains.rendering.api.router import create_rendering_router
from domains.agent.api.router import create_agent_router
from domains.web_access.api.router import create_web_access_router

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("presenton.launcher")


# ─── App factory ──────────────────────────────────────────────────────────────

def create_embedded_app() -> FastAPI:
    """Build the combined FastAPI app with all domain routers mounted."""

    engine = get_shared_engine()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("Presenton embedded backend starting …")
        # Domain-specific startup hooks can be added here.
        yield
        logger.info("Presenton embedded backend shutting down …")
        await engine.dispose()

    app = FastAPI(
        title="Presenton Embedded",
        version="1.0.0",
        description="All domains running in a single process (Electron mode).",
        lifespan=lifespan,
    )

    # Allow requests from the Next.js renderer (localhost only)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "app://.", "file://"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Mount domain routers ────────────────────────────────────────────────
    # Each router is instantiated with the shared engine and event bus so that
    # domain code never touches external services.

    shared_deps = dict(engine=engine, event_bus=shared_event_bus)

    app.include_router(
        create_identity_router(**shared_deps), prefix="/api/v1/identity", tags=["identity"]
    )
    app.include_router(
        create_auth_router(**shared_deps), prefix="/api/v1/auth", tags=["auth"]
    )
    app.include_router(
        create_presentation_router(**shared_deps),
        prefix="/api/v1/presentations",
        tags=["presentation"],
    )
    app.include_router(
        create_content_router(**shared_deps), prefix="/api/v1/content", tags=["content"]
    )
    app.include_router(
        create_style_router(**shared_deps), prefix="/api/v1/styles", tags=["style"]
    )
    app.include_router(
        create_media_router(**shared_deps), prefix="/api/v1/media", tags=["media"]
    )
    app.include_router(
        create_export_router(**shared_deps), prefix="/api/v1/export", tags=["export"]
    )
    app.include_router(
        create_rendering_router(**shared_deps),
        prefix="/api/v1/rendering",
        tags=["rendering"],
    )
    app.include_router(
        create_agent_router(**shared_deps), prefix="/api/v1/agent", tags=["agent"]
    )
    app.include_router(
        create_web_access_router(**shared_deps),
        prefix="/api/v1/web-access",
        tags=["web_access"],
    )

    # ── Health endpoint ─────────────────────────────────────────────────────

    @app.get("/health", tags=["meta"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "mode": "electron"}

    return app


# ─── Entry point ──────────────────────────────────────────────────────────────

async def main() -> None:
    if os.getenv("PRESENTON_ENV") != "electron":
        logger.warning(
            "PRESENTON_ENV is not 'electron'. "
            "This launcher is designed for Electron embedded mode only."
        )

    port = int(os.getenv("PRESENTON_PORT", "8000"))
    app = create_embedded_app()

    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="info",
        access_log=True,
        loop="asyncio",
    )
    server = uvicorn.Server(config)

    # Graceful shutdown on SIGTERM (sent by Electron ProcessManager)
    loop = asyncio.get_running_loop()

    def _handle_sigterm() -> None:
        logger.info("Received SIGTERM — initiating graceful shutdown …")
        server.should_exit = True

    loop.add_signal_handler(signal.SIGTERM, _handle_sigterm)

    logger.info("Starting Presenton embedded server on port %d …", port)
    await server.serve()
    logger.info("Server stopped.")


if __name__ == "__main__":
    asyncio.run(main())
