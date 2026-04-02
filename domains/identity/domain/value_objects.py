from __future__ import annotations

from dataclasses import dataclass

import bcrypt

from shared.domain.value_object import ValueObject


@dataclass(frozen=True)
class Email(ValueObject):
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", self.value.lower().strip())


@dataclass(frozen=True)
class HashedPassword(ValueObject):
    hash_value: str

    @classmethod
    def from_plain(cls, plain: str) -> HashedPassword:
        hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
        return cls(hash_value=hashed)

    def verify(self, plain: str) -> bool:
        return bcrypt.checkpw(plain.encode(), self.hash_value.encode())


@dataclass(frozen=True)
class Permission(ValueObject):
    resource: str
    action: str
