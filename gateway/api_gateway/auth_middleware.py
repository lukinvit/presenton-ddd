"""JWT authentication middleware."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

# Paths that skip JWT validation
_PUBLIC_PATHS: frozenset[str] = frozenset(
    [
        "/api/v1/identity/register",
        "/api/v1/identity/login",
        "/health",
    ]
)


@dataclass
class UserContext:
    sub: str
    email: str | None = None
    roles: list[str] | None = None
    raw: dict[str, Any] | None = None


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """Validates Bearer JWT tokens on every request except public paths.

    Args:
        public_key: RSA public key (PEM string) used to verify token signatures.
        algorithm: JWT algorithm (default RS256).
        public_paths: Iterable of path prefixes that bypass auth.
    """

    def __init__(
        self,
        app,
        public_key: str,
        algorithm: str = "RS256",
        public_paths: frozenset[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.public_key = public_key
        self.algorithm = algorithm
        self.public_paths: frozenset[str] = (
            public_paths if public_paths is not None else _PUBLIC_PATHS
        )

    def _is_public(self, path: str) -> bool:
        return any(path == p or path.startswith(p + "/") for p in self.public_paths)

    def _decode_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(
            token,
            self.public_key,
            algorithms=[self.algorithm],
            options={"require": ["sub", "exp"]},
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._is_public(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header[len("Bearer ") :]
        try:
            payload = self._decode_token(token)
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"detail": "Token has expired"})
        except jwt.InvalidTokenError as exc:
            return JSONResponse(status_code=401, content={"detail": f"Invalid token: {exc}"})

        request.state.user = UserContext(
            sub=payload["sub"],
            email=payload.get("email"),
            roles=payload.get("roles", []),
            raw=payload,
        )
        return await call_next(request)
