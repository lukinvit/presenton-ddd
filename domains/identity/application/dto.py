from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TokenPairDTO:
    access_token: str
    refresh_token: str


@dataclass
class UserDTO:
    id: str
    email: str
    roles: list[str]
