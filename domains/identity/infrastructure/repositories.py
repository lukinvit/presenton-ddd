"""SQLModel-backed implementation of UserRepository."""

from __future__ import annotations

import json
import uuid

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlmodel import select

from domains.identity.domain.entities import Role, User
from domains.identity.domain.value_objects import Email, HashedPassword
from domains.identity.infrastructure.db_models import UserModel


def _model_to_entity(model: UserModel) -> User:
    role_names: list[str] = json.loads(model.roles_json)
    roles = [Role(id=uuid.uuid4(), name=name) for name in role_names]
    return User(
        id=model.id,
        email=Email(value=model.email),
        password=HashedPassword(hash_value=model.password_hash),
        roles=roles,
        created_at=model.created_at,
    )


def _entity_to_model(user: User) -> UserModel:
    role_names = [r.name for r in user.roles]
    return UserModel(
        id=user.id,
        email=user.email.value,
        password_hash=user.password.hash_value,
        roles_json=json.dumps(role_names),
        created_at=user.created_at,
    )


class SQLUserRepository:
    """Async SQLModel-backed repository for User aggregates."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def get(self, id: uuid.UUID) -> User | None:
        async with AsyncSession(self._engine) as session:
            result = await session.get(UserModel, id)
            if result is None:
                return None
            return _model_to_entity(result)

    async def get_by_email(self, email: str) -> User | None:
        async with AsyncSession(self._engine) as session:
            stmt = select(UserModel).where(UserModel.email == email.lower().strip())
            result = await session.exec(stmt)
            model = result.first()
            if model is None:
                return None
            return _model_to_entity(model)

    async def save(self, user: User) -> None:
        async with AsyncSession(self._engine) as session:
            existing = await session.get(UserModel, user.id)
            if existing is not None:
                # Update fields in-place
                existing.email = user.email.value
                existing.password_hash = user.password.hash_value
                existing.roles_json = json.dumps([r.name for r in user.roles])
                session.add(existing)
            else:
                session.add(_entity_to_model(user))
            await session.commit()

    async def delete(self, id: uuid.UUID) -> None:
        async with AsyncSession(self._engine) as session:
            model = await session.get(UserModel, id)
            if model is not None:
                await session.delete(model)
                await session.commit()
