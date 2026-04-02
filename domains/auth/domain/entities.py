from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from shared.domain.entity import AggregateRoot
from .value_objects import EncryptedToken, OAuthProvider


@dataclass
class OAuthConnection(AggregateRoot):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    provider: OAuthProvider = OAuthProvider.ANTHROPIC
    access_token: EncryptedToken = field(default_factory=lambda: EncryptedToken(value=""))
    refresh_token: EncryptedToken | None = None
    expires_at: datetime | None = None

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > (self.expires_at - timedelta(seconds=buffer_seconds))
