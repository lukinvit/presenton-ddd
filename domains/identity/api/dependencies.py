from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from domains.identity.domain.services import TokenService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None
) -> dict[str, Any]:  # noqa: B008
    token_service: TokenService = request.app.state.token_service
    try:
        payload = token_service.verify_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from e


def require_role(role: str):
    async def check_role(user: dict = Depends(get_current_user)) -> dict:  # noqa: B008
        if role not in user.get("roles", []):
            raise HTTPException(status_code=403, detail=f"Role '{role}' required")
        return user

    return check_role
