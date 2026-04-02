from __future__ import annotations
import uuid
from dataclasses import dataclass
from shared.domain.events import DomainEvent, EventBus
from domain.entities import User
from domain.events import EVENT_USER_LOGGED_IN, EVENT_USER_REGISTERED
from domain.repositories import UserRepository
from domain.services import TokenService
from domain.value_objects import Email, HashedPassword
from application.dto import TokenPairDTO


@dataclass
class RegisterUserCommand:
    user_repo: UserRepository
    event_bus: EventBus
    token_service: TokenService

    async def execute(self, email: str, password: str) -> TokenPairDTO:
        existing = await self.user_repo.get_by_email(email.lower().strip())
        if existing is not None:
            raise ValueError(f"Email '{email}' is already registered")
        user = User(
            id=uuid.uuid4(),
            email=Email(value=email),
            password=HashedPassword.from_plain(password),
            roles=[],
        )
        await self.user_repo.save(user)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=user.id,
                event_type=EVENT_USER_REGISTERED,
                payload={"user_id": str(user.id), "email": user.email.value},
            )
        )
        access = self.token_service.create_access_token(user_id=user.id, roles=[])
        refresh = self.token_service.create_refresh_token(user_id=user.id)
        return TokenPairDTO(access_token=access, refresh_token=refresh)


@dataclass
class LoginUserCommand:
    user_repo: UserRepository
    event_bus: EventBus
    token_service: TokenService

    async def execute(self, email: str, password: str) -> TokenPairDTO:
        user = await self.user_repo.get_by_email(email.lower().strip())
        if user is None:
            raise ValueError("Invalid credentials")
        if not user.password.verify(password):
            raise ValueError("Invalid credentials")
        role_names = [r.name for r in user.roles]
        access = self.token_service.create_access_token(user_id=user.id, roles=role_names)
        refresh = self.token_service.create_refresh_token(user_id=user.id)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=user.id,
                event_type=EVENT_USER_LOGGED_IN,
                payload={"user_id": str(user.id), "email": user.email.value},
            )
        )
        return TokenPairDTO(access_token=access, refresh_token=refresh)
