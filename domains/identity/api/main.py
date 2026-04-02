"""Identity domain — FastAPI application entry point."""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import AsyncSession

from domains.identity.api.router import create_identity_router
from domains.identity.domain.services import TokenService
from domains.identity.domain.value_objects import Email, HashedPassword
from domains.identity.domain.entities import User
from domains.identity.infrastructure.db_models import UserModel  # registers table metadata
from domains.identity.infrastructure.repositories import SQLUserRepository
from shared.infrastructure.config import get_settings
from shared.infrastructure.database import DatabaseConfig, create_engine_from_config
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus

_ADMIN_EMAIL = "admin@presenton.ai"
_ADMIN_PASSWORD = "admin123"


def create_app() -> FastAPI:
    settings = get_settings()

    engine = create_engine_from_config(DatabaseConfig(url=settings.database_url))
    event_bus = InMemoryEventBus()

    # HS256 symmetric JWT — same secret used for sign and verify
    jwt_secret = os.getenv("PRESENTON_JWT_SECRET", settings.jwt_secret) or "change-this-jwt-secret"
    token_service = TokenService(
        private_key=jwt_secret,
        public_key=jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    user_repo = SQLUserRepository(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        # Create tables on startup
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Seed default admin user if the users table is empty
        async with AsyncSession(engine) as session:
            result = await session.exec(select(UserModel).limit(1))
            if result.first() is None:
                admin = User(
                    id=uuid.uuid4(),
                    email=Email(value=_ADMIN_EMAIL),
                    password=HashedPassword.from_plain(_ADMIN_PASSWORD),
                    roles=[],
                )
                await user_repo.save(admin)

        yield
        await engine.dispose()

    app = FastAPI(
        title="Presenton — Identity Domain",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    router = create_identity_router(
        user_repo=user_repo,
        event_bus=event_bus,
        token_service=token_service,
    )
    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "domain": "identity"}

    return app


app = create_app()
