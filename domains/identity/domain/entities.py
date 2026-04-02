from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from shared.domain.entity import AggregateRoot, Entity

from .value_objects import Email, HashedPassword, Permission


@dataclass
class Role(Entity):
    name: str = ""
    permissions: list[Permission] = field(default_factory=list)

    def has_permission(self, resource: str, action: str) -> bool:
        return any(p.resource == resource and p.action == action for p in self.permissions)


@dataclass
class Session(Entity):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    expires_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at


@dataclass
class User(AggregateRoot):
    email: Email = field(default_factory=lambda: Email(value=""))
    password: HashedPassword = field(default_factory=lambda: HashedPassword(hash_value=""))
    roles: list[Role] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def has_role(self, role_name: str) -> bool:
        return any(r.name == role_name for r in self.roles)
