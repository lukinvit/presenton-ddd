"""SQLModel table models for the identity domain."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class UserModel(SQLModel, table=True):
    __tablename__ = "identity_users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    roles_json: str = Field(default="[]")  # JSON array of role names
    created_at: datetime = Field(default_factory=datetime.utcnow)
