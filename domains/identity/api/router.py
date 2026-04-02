from __future__ import annotations

from fastapi import APIRouter, HTTPException

from domains.identity.api.schemas import LoginRequest, RegisterRequest, TokenPairResponse
from domains.identity.application.commands import LoginUserCommand, RegisterUserCommand
from domains.identity.domain.repositories import UserRepository
from domains.identity.domain.services import TokenService
from shared.domain.events import EventBus


def create_identity_router(
    user_repo: UserRepository, event_bus: EventBus, token_service: TokenService
) -> APIRouter:
    router = APIRouter(tags=["identity"])

    @router.post("/register", response_model=TokenPairResponse, status_code=201)
    async def register(req: RegisterRequest) -> TokenPairResponse:
        cmd = RegisterUserCommand(
            user_repo=user_repo, event_bus=event_bus, token_service=token_service
        )
        try:
            result = await cmd.execute(email=req.email, password=req.password)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e)) from e
        return TokenPairResponse(
            access_token=result.access_token, refresh_token=result.refresh_token
        )

    @router.post("/login", response_model=TokenPairResponse)
    async def login(req: LoginRequest) -> TokenPairResponse:
        cmd = LoginUserCommand(
            user_repo=user_repo, event_bus=event_bus, token_service=token_service
        )
        try:
            result = await cmd.execute(email=req.email, password=req.password)
        except ValueError as e:
            raise HTTPException(status_code=401, detail="Invalid credentials") from e
        return TokenPairResponse(
            access_token=result.access_token, refresh_token=result.refresh_token
        )

    return router
