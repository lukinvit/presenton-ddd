from __future__ import annotations
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt


class TokenService:
    """JWT token creation and verification using RS256."""
    ACCESS_TOKEN_TTL = timedelta(minutes=15)
    REFRESH_TOKEN_TTL = timedelta(days=7)

    def __init__(self, private_key: str, public_key: str, algorithm: str = "RS256") -> None:
        self._private_key = private_key
        self._public_key = public_key
        self._algorithm = algorithm

    def create_access_token(self, user_id: uuid.UUID, roles: list[str], ttl: timedelta | None = None) -> str:
        now = datetime.now(timezone.utc)
        exp = now + (ttl if ttl is not None else self.ACCESS_TOKEN_TTL)
        payload = {"sub": str(user_id), "roles": roles, "type": "access", "iat": now, "exp": exp}
        return jwt.encode(payload, self._private_key, algorithm=self._algorithm)

    def create_refresh_token(self, user_id: uuid.UUID, ttl: timedelta | None = None) -> str:
        now = datetime.now(timezone.utc)
        exp = now + (ttl if ttl is not None else self.REFRESH_TOKEN_TTL)
        payload = {"sub": str(user_id), "type": "refresh", "iat": now, "exp": exp, "jti": str(uuid.uuid4())}
        return jwt.encode(payload, self._private_key, algorithm=self._algorithm)

    def verify_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self._public_key, algorithms=[self._algorithm])
