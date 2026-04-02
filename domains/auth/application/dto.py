from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OAuthURLDTO:
    authorize_url: str
    state: str


@dataclass
class ConnectionStatusDTO:
    provider: str
    connected: bool
    expires_at: str | None = None
