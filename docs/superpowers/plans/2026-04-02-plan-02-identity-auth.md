# Plan 2: Identity + Auth Domains

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build user authentication (Identity domain) and OAuth provider connections (Auth domain) — JWT + RBAC for users, OAuth 2.0 + PKCE for Anthropic/OpenAI, encrypted storage for API keys.

**Architecture:** Two separate domains following the shared kernel patterns from Plan 1. Identity handles user registration/login/sessions/RBAC. Auth handles OAuth flows to AI providers and encrypted token storage. Both expose FastAPI endpoints and MCP tools. Identity provides JWT middleware consumed by all other domains via shared helper.

**Tech Stack:** Python 3.11, FastAPI, SQLModel, Alembic, bcrypt, PyJWT (RS256), cryptography (AES-256), httpx (OAuth flows), pytest

**Depends on:** Plan 1 (Shared Kernel) must be completed first.

---

## File Structure

```
domains/
├── identity/
│   ├── pyproject.toml
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities.py          # User, Session, Role
│   │   ├── value_objects.py     # Email, HashedPassword, Permission
│   │   ├── events.py            # UserRegistered, UserLoggedIn
│   │   ├── repositories.py      # UserRepository, SessionRepository
│   │   └── services.py          # PasswordService, TokenService
│   ├── application/
│   │   ├── __init__.py
│   │   ├── commands.py          # RegisterUser, LoginUser, AssignRole
│   │   ├── queries.py           # GetUser, ListUsers, VerifySession
│   │   └── dto.py               # UserDTO, TokenPairDTO
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── db/
│   │   │   ├── models.py        # SQLModel tables
│   │   │   ├── repositories.py  # SQL implementations
│   │   │   └── migrations/      # Alembic
│   │   └── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── schemas.py
│   │   └── dependencies.py      # get_current_user, require_role
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── server.py
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_entities.py
│   │   │   ├── test_password_service.py
│   │   │   └── test_token_service.py
│   │   ├── integration/
│   │   │   ├── test_api.py
│   │   │   └── test_repositories.py
│   │   └── conftest.py
│   └── Dockerfile
├── auth/
│   ├── pyproject.toml
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities.py          # OAuthConnection, ProviderConfig
│   │   ├── value_objects.py     # EncryptedToken, OAuthState
│   │   ├── events.py            # ProviderConnected, TokenRefreshed
│   │   ├── repositories.py      # OAuthConnectionRepository
│   │   └── services.py          # EncryptionService, OAuthFlowService
│   ├── application/
│   │   ├── __init__.py
│   │   ├── commands.py          # InitiateOAuth, HandleCallback, RefreshToken, DisconnectProvider
│   │   ├── queries.py           # GetToken, GetConnectionStatus
│   │   └── dto.py               # OAuthURLDTO, TokenDTO, ConnectionStatusDTO
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── db/
│   │   │   ├── models.py
│   │   │   ├── repositories.py
│   │   │   └── migrations/
│   │   ├── providers/
│   │   │   ├── anthropic_oauth.py
│   │   │   ├── openai_oauth.py
│   │   │   └── api_key_provider.py  # For Gemini/Ollama/Custom
│   │   └── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── schemas.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── server.py
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_encryption_service.py
│   │   │   ├── test_oauth_flow.py
│   │   │   └── test_entities.py
│   │   ├── integration/
│   │   │   ├── test_api.py
│   │   │   └── test_repositories.py
│   │   └── conftest.py
│   └── Dockerfile
```

---

### Task 1: Identity Domain — Entities and Value Objects

**Files:**
- Create: `domains/identity/pyproject.toml`
- Create: `domains/identity/domain/__init__.py`
- Create: `domains/identity/domain/entities.py`
- Create: `domains/identity/domain/value_objects.py`
- Create: `domains/identity/domain/events.py`
- Test: `domains/identity/tests/unit/test_entities.py`

- [ ] **Step 1: Create identity pyproject.toml**

```toml
[project]
name = "presenton-identity"
version = "0.1.0"
description = "Identity bounded context — users, sessions, RBAC"
requires-python = ">=3.11,<3.13"
dependencies = [
    "presenton-shared",
    "fastapi[standard]>=0.116.0",
    "sqlmodel>=0.0.24",
    "alembic>=1.14.0",
    "bcrypt>=4.2.0",
    "PyJWT[crypto]>=2.9.0",
    "httpx>=0.28.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.24.0", "httpx>=0.28.0"]
```

- [ ] **Step 2: Write the failing test**

```python
# domains/identity/tests/unit/test_entities.py
import uuid
from datetime import datetime, timezone, timedelta
from domains.identity.domain.entities import User, Session, Role
from domains.identity.domain.value_objects import Email, HashedPassword, Permission


class TestEmail:
    def test_valid_email(self) -> None:
        email = Email(value="user@example.com")
        assert email.value == "user@example.com"

    def test_email_equality(self) -> None:
        e1 = Email(value="user@example.com")
        e2 = Email(value="user@example.com")
        assert e1 == e2

    def test_email_case_insensitive(self) -> None:
        e1 = Email(value="User@Example.COM")
        assert e1.value == "user@example.com"


class TestHashedPassword:
    def test_create_from_plain(self) -> None:
        hp = HashedPassword.from_plain("securepassword123")
        assert hp.hash_value != "securepassword123"
        assert hp.hash_value.startswith("$2b$")

    def test_verify_correct_password(self) -> None:
        hp = HashedPassword.from_plain("securepassword123")
        assert hp.verify("securepassword123") is True

    def test_verify_wrong_password(self) -> None:
        hp = HashedPassword.from_plain("securepassword123")
        assert hp.verify("wrongpassword") is False


class TestRole:
    def test_role_has_permissions(self) -> None:
        role = Role(
            id=uuid.uuid4(),
            name="editor",
            permissions=[
                Permission(resource="presentation", action="read"),
                Permission(resource="presentation", action="write"),
            ],
        )
        assert len(role.permissions) == 2

    def test_role_has_permission(self) -> None:
        role = Role(
            id=uuid.uuid4(),
            name="editor",
            permissions=[Permission(resource="presentation", action="read")],
        )
        assert role.has_permission("presentation", "read") is True
        assert role.has_permission("presentation", "delete") is False


class TestUser:
    def test_create_user(self) -> None:
        user = User(
            id=uuid.uuid4(),
            email=Email(value="test@example.com"),
            password=HashedPassword.from_plain("pass123"),
            roles=[],
        )
        assert user.email.value == "test@example.com"

    def test_user_has_role(self) -> None:
        role = Role(id=uuid.uuid4(), name="admin", permissions=[])
        user = User(
            id=uuid.uuid4(),
            email=Email(value="admin@example.com"),
            password=HashedPassword.from_plain("pass"),
            roles=[role],
        )
        assert user.has_role("admin") is True
        assert user.has_role("viewer") is False


class TestSession:
    def test_session_not_expired(self) -> None:
        session = Session(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        assert session.is_expired is False

    def test_session_expired(self) -> None:
        session = Session(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        assert session.is_expired is True
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest domains/identity/tests/unit/test_entities.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Write implementation**

```python
# domains/identity/domain/__init__.py
"""Identity domain layer."""
```

```python
# domains/identity/domain/value_objects.py
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
```

```python
# domains/identity/domain/entities.py
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from shared.domain.entity import AggregateRoot, Entity

from .value_objects import Email, HashedPassword, Permission


@dataclass
class Role(Entity):
    name: str = ""
    permissions: list[Permission] = field(default_factory=list)

    def has_permission(self, resource: str, action: str) -> bool:
        return any(
            p.resource == resource and p.action == action for p in self.permissions
        )


@dataclass
class Session(Entity):
    user_id: uuid.UUID = field(default_factory=uuid.uuid4)
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at


@dataclass
class User(AggregateRoot):
    email: Email = field(default_factory=lambda: Email(value=""))
    password: HashedPassword = field(
        default_factory=lambda: HashedPassword(hash_value="")
    )
    roles: list[Role] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def has_role(self, role_name: str) -> bool:
        return any(r.name == role_name for r in self.roles)
```

```python
# domains/identity/domain/events.py
"""Identity domain events — defined as event_type strings.

Events:
- UserRegistered: payload = {user_id, email}
- UserLoggedIn: payload = {user_id, email}
- RoleAssigned: payload = {user_id, role_name}
"""
EVENT_USER_REGISTERED = "UserRegistered"
EVENT_USER_LOGGED_IN = "UserLoggedIn"
EVENT_ROLE_ASSIGNED = "RoleAssigned"
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest domains/identity/tests/unit/test_entities.py -v`
Expected: All 11 tests PASS

- [ ] **Step 6: Commit**

```bash
git add domains/identity/
git commit -m "feat(identity): add User, Session, Role entities and value objects"
```

---

### Task 2: Identity Domain — Password and Token Services

**Files:**
- Create: `domains/identity/domain/services.py`
- Test: `domains/identity/tests/unit/test_password_service.py`
- Test: `domains/identity/tests/unit/test_token_service.py`

- [ ] **Step 1: Write the failing tests**

```python
# domains/identity/tests/unit/test_token_service.py
import uuid
import pytest
from datetime import timedelta
from domains.identity.domain.services import TokenService


class TestTokenService:
    def setup_method(self) -> None:
        # Generate RSA key pair for tests
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.private_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode()
        self.public_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()
        self.service = TokenService(
            private_key=self.private_pem,
            public_key=self.public_pem,
            algorithm="RS256",
        )

    def test_create_access_token(self) -> None:
        user_id = uuid.uuid4()
        token = self.service.create_access_token(
            user_id=user_id, roles=["editor"]
        )
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token(self) -> None:
        user_id = uuid.uuid4()
        token = self.service.create_access_token(
            user_id=user_id, roles=["editor"]
        )
        payload = self.service.verify_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["roles"] == ["editor"]
        assert payload["type"] == "access"

    def test_create_refresh_token(self) -> None:
        user_id = uuid.uuid4()
        token = self.service.create_refresh_token(user_id=user_id)
        payload = self.service.verify_token(token)
        assert payload["type"] == "refresh"

    def test_expired_token_raises(self) -> None:
        user_id = uuid.uuid4()
        token = self.service.create_access_token(
            user_id=user_id, roles=[], ttl=timedelta(seconds=-1)
        )
        with pytest.raises(Exception):
            self.service.verify_token(token)

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(Exception):
            self.service.verify_token("invalid.token.here")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest domains/identity/tests/unit/test_token_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# domains/identity/domain/services.py
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

    def create_access_token(
        self,
        user_id: uuid.UUID,
        roles: list[str],
        ttl: timedelta | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        exp = now + (ttl if ttl is not None else self.ACCESS_TOKEN_TTL)
        payload = {
            "sub": str(user_id),
            "roles": roles,
            "type": "access",
            "iat": now,
            "exp": exp,
        }
        return jwt.encode(payload, self._private_key, algorithm=self._algorithm)

    def create_refresh_token(
        self,
        user_id: uuid.UUID,
        ttl: timedelta | None = None,
    ) -> str:
        now = datetime.now(timezone.utc)
        exp = now + (ttl if ttl is not None else self.REFRESH_TOKEN_TTL)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": now,
            "exp": exp,
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, self._private_key, algorithm=self._algorithm)

    def verify_token(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self._public_key, algorithms=[self._algorithm])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest domains/identity/tests/unit/test_token_service.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add domains/identity/domain/services.py domains/identity/tests/unit/test_token_service.py
git commit -m "feat(identity): add TokenService with RS256 JWT creation and verification"
```

---

### Task 3: Identity Domain — Commands (Register, Login)

**Files:**
- Create: `domains/identity/domain/repositories.py`
- Create: `domains/identity/application/__init__.py`
- Create: `domains/identity/application/dto.py`
- Create: `domains/identity/application/commands.py`
- Test: `domains/identity/tests/unit/test_commands.py`

- [ ] **Step 1: Write the failing test**

```python
# domains/identity/tests/unit/test_commands.py
import uuid
import pytest
from unittest.mock import AsyncMock
from domains.identity.application.commands import RegisterUserCommand, LoginUserCommand
from domains.identity.application.dto import TokenPairDTO
from domains.identity.domain.entities import User
from domains.identity.domain.value_objects import Email, HashedPassword


class TestRegisterUserCommand:
    @pytest.mark.asyncio
    async def test_register_creates_user(self) -> None:
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=None)
        user_repo.save = AsyncMock()
        event_bus = AsyncMock()
        token_service = AsyncMock()
        token_service.create_access_token.return_value = "access_token"
        token_service.create_refresh_token.return_value = "refresh_token"

        cmd = RegisterUserCommand(
            user_repo=user_repo,
            event_bus=event_bus,
            token_service=token_service,
        )
        result = await cmd.execute(email="new@example.com", password="secret123")

        assert isinstance(result, TokenPairDTO)
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"
        user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(self) -> None:
        existing = User(
            id=uuid.uuid4(),
            email=Email(value="exists@example.com"),
            password=HashedPassword.from_plain("pass"),
        )
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=existing)

        cmd = RegisterUserCommand(
            user_repo=user_repo,
            event_bus=AsyncMock(),
            token_service=AsyncMock(),
        )
        with pytest.raises(ValueError, match="already registered"):
            await cmd.execute(email="exists@example.com", password="secret123")


class TestLoginUserCommand:
    @pytest.mark.asyncio
    async def test_login_success(self) -> None:
        user = User(
            id=uuid.uuid4(),
            email=Email(value="user@example.com"),
            password=HashedPassword.from_plain("correct_pass"),
            roles=[],
        )
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=user)
        event_bus = AsyncMock()
        token_service = AsyncMock()
        token_service.create_access_token.return_value = "access"
        token_service.create_refresh_token.return_value = "refresh"

        cmd = LoginUserCommand(
            user_repo=user_repo,
            event_bus=event_bus,
            token_service=token_service,
        )
        result = await cmd.execute(email="user@example.com", password="correct_pass")
        assert result.access_token == "access"

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises(self) -> None:
        user = User(
            id=uuid.uuid4(),
            email=Email(value="user@example.com"),
            password=HashedPassword.from_plain("correct_pass"),
        )
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=user)

        cmd = LoginUserCommand(
            user_repo=user_repo,
            event_bus=AsyncMock(),
            token_service=AsyncMock(),
        )
        with pytest.raises(ValueError, match="Invalid credentials"):
            await cmd.execute(email="user@example.com", password="wrong_pass")

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_raises(self) -> None:
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=None)

        cmd = LoginUserCommand(
            user_repo=user_repo,
            event_bus=AsyncMock(),
            token_service=AsyncMock(),
        )
        with pytest.raises(ValueError, match="Invalid credentials"):
            await cmd.execute(email="nobody@example.com", password="pass")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest domains/identity/tests/unit/test_commands.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# domains/identity/domain/repositories.py
from __future__ import annotations

import uuid
from typing import Protocol

from .entities import User


class UserRepository(Protocol):
    async def get(self, id: uuid.UUID) -> User | None: ...
    async def get_by_email(self, email: str) -> User | None: ...
    async def save(self, user: User) -> None: ...
    async def delete(self, id: uuid.UUID) -> None: ...
```

```python
# domains/identity/application/__init__.py
"""Identity application layer."""
```

```python
# domains/identity/application/dto.py
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
```

```python
# domains/identity/application/commands.py
from __future__ import annotations

import uuid
from dataclasses import dataclass

from shared.domain.events import DomainEvent, EventBus

from ..domain.entities import User
from ..domain.events import EVENT_USER_LOGGED_IN, EVENT_USER_REGISTERED
from ..domain.repositories import UserRepository
from ..domain.services import TokenService
from ..domain.value_objects import Email, HashedPassword
from .dto import TokenPairDTO


@dataclass
class RegisterUserCommand:
    user_repo: UserRepository
    event_bus: EventBus
    token_service: TokenService

    async def execute(self, email: str, password: str) -> TokenPairDTO:
        existing = await self.user_repo.get_by_email(email.lower().strip())
        if existing is not None:
            raise ValueError(f"Email '{email}' is already registered")

        user = User(
            id=uuid.uuid4(),
            email=Email(value=email),
            password=HashedPassword.from_plain(password),
            roles=[],
        )
        await self.user_repo.save(user)
        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=user.id,
                event_type=EVENT_USER_REGISTERED,
                payload={"user_id": str(user.id), "email": user.email.value},
            )
        )

        access = self.token_service.create_access_token(user_id=user.id, roles=[])
        refresh = self.token_service.create_refresh_token(user_id=user.id)
        return TokenPairDTO(access_token=access, refresh_token=refresh)


@dataclass
class LoginUserCommand:
    user_repo: UserRepository
    event_bus: EventBus
    token_service: TokenService

    async def execute(self, email: str, password: str) -> TokenPairDTO:
        user = await self.user_repo.get_by_email(email.lower().strip())
        if user is None:
            raise ValueError("Invalid credentials")

        if not user.password.verify(password):
            raise ValueError("Invalid credentials")

        role_names = [r.name for r in user.roles]
        access = self.token_service.create_access_token(
            user_id=user.id, roles=role_names
        )
        refresh = self.token_service.create_refresh_token(user_id=user.id)

        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=user.id,
                event_type=EVENT_USER_LOGGED_IN,
                payload={"user_id": str(user.id), "email": user.email.value},
            )
        )

        return TokenPairDTO(access_token=access, refresh_token=refresh)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest domains/identity/tests/unit/test_commands.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add domains/identity/
git commit -m "feat(identity): add RegisterUser and LoginUser commands with TDD"
```

---

### Task 4: Identity Domain — FastAPI Router

**Files:**
- Create: `domains/identity/api/__init__.py`
- Create: `domains/identity/api/schemas.py`
- Create: `domains/identity/api/dependencies.py`
- Create: `domains/identity/api/router.py`
- Test: `domains/identity/tests/integration/test_api.py`

- [ ] **Step 1: Write the failing test**

```python
# domains/identity/tests/integration/test_api.py
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from domains.identity.api.router import create_identity_router
from unittest.mock import AsyncMock


def create_test_app() -> FastAPI:
    app = FastAPI()
    user_repo = AsyncMock()
    user_repo.get_by_email = AsyncMock(return_value=None)
    user_repo.save = AsyncMock()
    event_bus = AsyncMock()

    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    ).decode()
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    from domains.identity.domain.services import TokenService
    token_service = TokenService(private_key=private_pem, public_key=public_pem)

    router = create_identity_router(user_repo, event_bus, token_service)
    app.include_router(router)
    return app


class TestIdentityAPI:
    @pytest.mark.asyncio
    async def test_register_endpoint(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/register", json={
                "email": "new@example.com",
                "password": "secret123",
            })
            assert resp.status_code == 201
            data = resp.json()
            assert "access_token" in data
            assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_register_invalid_email_returns_422(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/register", json={
                "email": "",
                "password": "secret123",
            })
            assert resp.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest domains/identity/tests/integration/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# domains/identity/api/__init__.py
"""Identity API layer."""
```

```python
# domains/identity/api/schemas.py
from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Email must not be empty")
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
```

```python
# domains/identity/api/dependencies.py
from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..domain.services import TokenService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None,
) -> dict[str, Any]:
    """Extract and verify JWT from Authorization header."""
    token_service: TokenService = request.app.state.token_service
    try:
        payload = token_service.verify_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_role(role: str):
    """Dependency factory: require the user to have a specific role."""
    async def check_role(user: dict = Depends(get_current_user)) -> dict:
        if role not in user.get("roles", []):
            raise HTTPException(status_code=403, detail=f"Role '{role}' required")
        return user
    return check_role
```

```python
# domains/identity/api/router.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from shared.domain.events import EventBus

from ..application.commands import LoginUserCommand, RegisterUserCommand
from ..domain.repositories import UserRepository
from ..domain.services import TokenService
from .schemas import LoginRequest, RegisterRequest, TokenPairResponse


def create_identity_router(
    user_repo: UserRepository,
    event_bus: EventBus,
    token_service: TokenService,
) -> APIRouter:
    router = APIRouter(tags=["identity"])

    @router.post("/register", response_model=TokenPairResponse, status_code=201)
    async def register(req: RegisterRequest) -> TokenPairResponse:
        cmd = RegisterUserCommand(
            user_repo=user_repo,
            event_bus=event_bus,
            token_service=token_service,
        )
        try:
            result = await cmd.execute(email=req.email, password=req.password)
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))
        return TokenPairResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
        )

    @router.post("/login", response_model=TokenPairResponse)
    async def login(req: LoginRequest) -> TokenPairResponse:
        cmd = LoginUserCommand(
            user_repo=user_repo,
            event_bus=event_bus,
            token_service=token_service,
        )
        try:
            result = await cmd.execute(email=req.email, password=req.password)
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return TokenPairResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
        )

    return router
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest domains/identity/tests/integration/test_api.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add domains/identity/api/
git commit -m "feat(identity): add FastAPI register/login endpoints"
```

---

### Task 5: Auth Domain — Encryption Service

**Files:**
- Create: `domains/auth/pyproject.toml`
- Create: `domains/auth/domain/__init__.py`
- Create: `domains/auth/domain/services.py`
- Test: `domains/auth/tests/unit/test_encryption_service.py`

- [ ] **Step 1: Create auth pyproject.toml**

```toml
[project]
name = "presenton-auth"
version = "0.1.0"
description = "Auth bounded context — OAuth to AI providers, encrypted token storage"
requires-python = ">=3.11,<3.13"
dependencies = [
    "presenton-shared",
    "fastapi[standard]>=0.116.0",
    "sqlmodel>=0.0.24",
    "alembic>=1.14.0",
    "cryptography>=44.0.0",
    "httpx>=0.28.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.24.0", "httpx>=0.28.0"]
```

- [ ] **Step 2: Write the failing test**

```python
# domains/auth/tests/unit/test_encryption_service.py
import pytest
from domains.auth.domain.services import EncryptionService


class TestEncryptionService:
    def setup_method(self) -> None:
        # 32-byte key for AES-256
        self.key = "a" * 32
        self.service = EncryptionService(key=self.key)

    def test_encrypt_returns_different_from_plaintext(self) -> None:
        encrypted = self.service.encrypt("my_secret_token")
        assert encrypted != "my_secret_token"

    def test_decrypt_returns_original(self) -> None:
        original = "sk-ant-api03-xxxxx"
        encrypted = self.service.encrypt(original)
        decrypted = self.service.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_same_text_produces_different_ciphertexts(self) -> None:
        """AES-GCM uses random nonce, so same plaintext → different ciphertext."""
        e1 = self.service.encrypt("same")
        e2 = self.service.encrypt("same")
        assert e1 != e2

    def test_decrypt_with_wrong_key_raises(self) -> None:
        encrypted = self.service.encrypt("secret")
        wrong_service = EncryptionService(key="b" * 32)
        with pytest.raises(Exception):
            wrong_service.decrypt(encrypted)

    def test_encrypt_empty_string(self) -> None:
        encrypted = self.service.encrypt("")
        decrypted = self.service.decrypt(encrypted)
        assert decrypted == ""
```

- [ ] **Step 3: Run test to verify it fails**

Run: `uv run pytest domains/auth/tests/unit/test_encryption_service.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Write implementation**

```python
# domains/auth/domain/__init__.py
"""Auth domain layer."""
```

```python
# domains/auth/domain/services.py
from __future__ import annotations

import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    """AES-256-GCM encryption for token storage."""

    NONCE_SIZE = 12  # 96-bit nonce for GCM

    def __init__(self, key: str) -> None:
        # Ensure key is exactly 32 bytes
        key_bytes = key.encode("utf-8")[:32].ljust(32, b"\0")
        self._aesgcm = AESGCM(key_bytes)

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(self.NONCE_SIZE)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        # Encode nonce + ciphertext as base64
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt(self, encrypted: str) -> str:
        raw = base64.b64decode(encrypted.encode("utf-8"))
        nonce = raw[: self.NONCE_SIZE]
        ciphertext = raw[self.NONCE_SIZE :]
        plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest domains/auth/tests/unit/test_encryption_service.py -v`
Expected: All 5 tests PASS

- [ ] **Step 6: Commit**

```bash
git add domains/auth/
git commit -m "feat(auth): add EncryptionService with AES-256-GCM"
```

---

### Task 6: Auth Domain — OAuth Entities and Flow

**Files:**
- Create: `domains/auth/domain/entities.py`
- Create: `domains/auth/domain/value_objects.py`
- Create: `domains/auth/domain/repositories.py`
- Create: `domains/auth/application/__init__.py`
- Create: `domains/auth/application/dto.py`
- Create: `domains/auth/application/commands.py`
- Create: `domains/auth/application/queries.py`
- Test: `domains/auth/tests/unit/test_oauth_flow.py`

- [ ] **Step 1: Write the failing test**

```python
# domains/auth/tests/unit/test_oauth_flow.py
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from domains.auth.domain.entities import OAuthConnection
from domains.auth.domain.value_objects import EncryptedToken, OAuthProvider
from domains.auth.application.commands import InitiateOAuthCommand, HandleCallbackCommand
from domains.auth.application.dto import OAuthURLDTO


class TestOAuthProvider:
    def test_anthropic_provider(self) -> None:
        provider = OAuthProvider.ANTHROPIC
        assert provider.value == "anthropic"

    def test_openai_provider(self) -> None:
        provider = OAuthProvider.OPENAI
        assert provider.value == "openai"

    def test_gemini_provider(self) -> None:
        provider = OAuthProvider.GEMINI
        assert provider.value == "gemini"


class TestOAuthConnection:
    def test_create_connection(self) -> None:
        conn = OAuthConnection(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            provider=OAuthProvider.ANTHROPIC,
            access_token=EncryptedToken(value="encrypted_access"),
            refresh_token=EncryptedToken(value="encrypted_refresh"),
            expires_at=None,
        )
        assert conn.provider == OAuthProvider.ANTHROPIC

    def test_is_expired_none_means_no_expiry(self) -> None:
        conn = OAuthConnection(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            provider=OAuthProvider.GEMINI,
            access_token=EncryptedToken(value="enc"),
            refresh_token=None,
            expires_at=None,
        )
        assert conn.is_expired(buffer_seconds=300) is False


class TestInitiateOAuthCommand:
    @pytest.mark.asyncio
    async def test_generates_authorize_url(self) -> None:
        oauth_provider_adapter = AsyncMock()
        oauth_provider_adapter.get_authorize_url.return_value = (
            "https://console.anthropic.com/oauth/authorize?client_id=xxx&state=abc",
            "abc",  # state
            "verifier123",  # code_verifier
        )
        state_repo = AsyncMock()

        cmd = InitiateOAuthCommand(
            oauth_provider_adapter=oauth_provider_adapter,
            state_repo=state_repo,
        )
        result = await cmd.execute(
            provider="anthropic",
            user_id=uuid.uuid4(),
            redirect_uri="http://localhost:5000/api/v1/auth/callback",
        )

        assert isinstance(result, OAuthURLDTO)
        assert "anthropic.com" in result.authorize_url
        state_repo.save.assert_called_once()


class TestHandleCallbackCommand:
    @pytest.mark.asyncio
    async def test_exchanges_code_for_tokens(self) -> None:
        oauth_provider_adapter = AsyncMock()
        oauth_provider_adapter.exchange_code.return_value = {
            "access_token": "raw_access",
            "refresh_token": "raw_refresh",
            "expires_in": 3600,
        }
        state_repo = AsyncMock()
        state_repo.get_and_delete.return_value = {
            "provider": "anthropic",
            "user_id": str(uuid.uuid4()),
            "code_verifier": "verifier123",
        }
        connection_repo = AsyncMock()
        encryption_service = MagicMock()
        encryption_service.encrypt.side_effect = lambda x: f"enc_{x}"
        event_bus = AsyncMock()

        cmd = HandleCallbackCommand(
            oauth_provider_adapter=oauth_provider_adapter,
            state_repo=state_repo,
            connection_repo=connection_repo,
            encryption_service=encryption_service,
            event_bus=event_bus,
        )
        await cmd.execute(code="auth_code_123", state="abc")

        connection_repo.save.assert_called_once()
        saved = connection_repo.save.call_args[0][0]
        assert isinstance(saved, OAuthConnection)
        assert saved.access_token.value == "enc_raw_access"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest domains/auth/tests/unit/test_oauth_flow.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# domains/auth/domain/value_objects.py
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from shared.domain.value_object import ValueObject


class OAuthProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    CUSTOM = "custom"


@dataclass(frozen=True)
class EncryptedToken(ValueObject):
    value: str
```

```python
# domains/auth/domain/entities.py
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

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
        from datetime import timedelta
        return datetime.now(timezone.utc) > (self.expires_at - timedelta(seconds=buffer_seconds))
```

```python
# domains/auth/domain/repositories.py
from __future__ import annotations

import uuid
from typing import Any, Protocol

from .entities import OAuthConnection
from .value_objects import OAuthProvider


class OAuthConnectionRepository(Protocol):
    async def get(self, id: uuid.UUID) -> OAuthConnection | None: ...
    async def get_by_user_and_provider(
        self, user_id: uuid.UUID, provider: OAuthProvider
    ) -> OAuthConnection | None: ...
    async def save(self, connection: OAuthConnection) -> None: ...
    async def delete(self, id: uuid.UUID) -> None: ...


class OAuthStateRepository(Protocol):
    """Temporary storage for OAuth state during the flow."""
    async def save(self, state: str, data: dict[str, Any]) -> None: ...
    async def get_and_delete(self, state: str) -> dict[str, Any] | None: ...
```

```python
# domains/auth/application/__init__.py
"""Auth application layer."""
```

```python
# domains/auth/application/dto.py
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
```

```python
# domains/auth/application/commands.py
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from shared.domain.events import DomainEvent, EventBus

from ..domain.entities import OAuthConnection
from ..domain.repositories import OAuthConnectionRepository, OAuthStateRepository
from ..domain.services import EncryptionService
from ..domain.value_objects import EncryptedToken, OAuthProvider
from .dto import OAuthURLDTO


class OAuthProviderAdapter(Protocol):
    async def get_authorize_url(
        self, redirect_uri: str
    ) -> tuple[str, str, str]: ...

    async def exchange_code(
        self, code: str, code_verifier: str, redirect_uri: str
    ) -> dict[str, Any]: ...


@dataclass
class InitiateOAuthCommand:
    oauth_provider_adapter: OAuthProviderAdapter
    state_repo: OAuthStateRepository

    async def execute(
        self, provider: str, user_id: uuid.UUID, redirect_uri: str
    ) -> OAuthURLDTO:
        authorize_url, state, code_verifier = (
            await self.oauth_provider_adapter.get_authorize_url(redirect_uri)
        )
        await self.state_repo.save(
            state,
            {
                "provider": provider,
                "user_id": str(user_id),
                "code_verifier": code_verifier,
            },
        )
        return OAuthURLDTO(authorize_url=authorize_url, state=state)


@dataclass
class HandleCallbackCommand:
    oauth_provider_adapter: OAuthProviderAdapter
    state_repo: OAuthStateRepository
    connection_repo: OAuthConnectionRepository
    encryption_service: EncryptionService
    event_bus: EventBus

    async def execute(self, code: str, state: str) -> None:
        state_data = await self.state_repo.get_and_delete(state)
        if state_data is None:
            raise ValueError("Invalid or expired OAuth state")

        tokens = await self.oauth_provider_adapter.exchange_code(
            code=code,
            code_verifier=state_data["code_verifier"],
            redirect_uri="",  # Will be set by adapter
        )

        provider = OAuthProvider(state_data["provider"])
        user_id = uuid.UUID(state_data["user_id"])

        expires_at = None
        if "expires_in" in tokens and tokens["expires_in"]:
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=tokens["expires_in"]
            )

        connection = OAuthConnection(
            id=uuid.uuid4(),
            user_id=user_id,
            provider=provider,
            access_token=EncryptedToken(
                value=self.encryption_service.encrypt(tokens["access_token"])
            ),
            refresh_token=EncryptedToken(
                value=self.encryption_service.encrypt(tokens["refresh_token"])
            )
            if tokens.get("refresh_token")
            else None,
            expires_at=expires_at,
        )
        await self.connection_repo.save(connection)

        await self.event_bus.publish(
            DomainEvent(
                aggregate_id=connection.id,
                event_type="ProviderConnected",
                payload={"user_id": str(user_id), "provider": provider.value},
            )
        )
```

```python
# domains/auth/application/queries.py
from __future__ import annotations

import uuid
from dataclasses import dataclass

from ..domain.repositories import OAuthConnectionRepository
from ..domain.services import EncryptionService
from ..domain.value_objects import OAuthProvider
from .dto import ConnectionStatusDTO


@dataclass
class GetTokenQuery:
    connection_repo: OAuthConnectionRepository
    encryption_service: EncryptionService

    async def execute(self, user_id: uuid.UUID, provider: str) -> str:
        oauth_provider = OAuthProvider(provider)
        conn = await self.connection_repo.get_by_user_and_provider(user_id, oauth_provider)
        if conn is None:
            raise ValueError(f"No connection for provider '{provider}'")
        return self.encryption_service.decrypt(conn.access_token.value)


@dataclass
class GetConnectionStatusQuery:
    connection_repo: OAuthConnectionRepository

    async def execute(self, user_id: uuid.UUID) -> list[ConnectionStatusDTO]:
        statuses = []
        for provider in OAuthProvider:
            conn = await self.connection_repo.get_by_user_and_provider(
                user_id, provider
            )
            statuses.append(
                ConnectionStatusDTO(
                    provider=provider.value,
                    connected=conn is not None,
                    expires_at=conn.expires_at.isoformat() if conn and conn.expires_at else None,
                )
            )
        return statuses
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest domains/auth/tests/unit/test_oauth_flow.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add domains/auth/
git commit -m "feat(auth): add OAuth entities, encryption, and command handlers"
```

---

### Task 7: Auth Domain — FastAPI Router

**Files:**
- Create: `domains/auth/api/__init__.py`
- Create: `domains/auth/api/router.py`
- Create: `domains/auth/api/schemas.py`
- Test: `domains/auth/tests/integration/test_api.py`

- [ ] **Step 1: Write the failing test**

```python
# domains/auth/tests/integration/test_api.py
import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock
from domains.auth.api.router import create_auth_router


def create_test_app() -> FastAPI:
    app = FastAPI()
    oauth_adapter = AsyncMock()
    oauth_adapter.get_authorize_url.return_value = (
        "https://console.anthropic.com/oauth/authorize?state=test",
        "test_state",
        "test_verifier",
    )
    state_repo = AsyncMock()
    connection_repo = AsyncMock()
    encryption_service = MagicMock()
    event_bus = AsyncMock()

    router = create_auth_router(
        oauth_adapters={"anthropic": oauth_adapter},
        state_repo=state_repo,
        connection_repo=connection_repo,
        encryption_service=encryption_service,
        event_bus=event_bus,
    )
    app.include_router(router)
    return app


class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_initiate_oauth(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/connect", json={
                "provider": "anthropic",
                "redirect_uri": "http://localhost:5000/api/v1/auth/callback",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "authorize_url" in data
            assert "anthropic.com" in data["authorize_url"]

    @pytest.mark.asyncio
    async def test_connect_unknown_provider_returns_400(self) -> None:
        app = create_test_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/connect", json={
                "provider": "nonexistent",
                "redirect_uri": "http://localhost:5000",
            })
            assert resp.status_code == 400
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest domains/auth/tests/integration/test_api.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write implementation**

```python
# domains/auth/api/__init__.py
"""Auth API layer."""
```

```python
# domains/auth/api/schemas.py
from pydantic import BaseModel


class ConnectRequest(BaseModel):
    provider: str
    redirect_uri: str


class ConnectResponse(BaseModel):
    authorize_url: str
    state: str


class CallbackRequest(BaseModel):
    code: str
    state: str


class StoreKeyRequest(BaseModel):
    provider: str
    api_key: str


class ConnectionStatusResponse(BaseModel):
    provider: str
    connected: bool
    expires_at: str | None = None
```

```python
# domains/auth/api/router.py
from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from shared.domain.events import EventBus

from ..application.commands import HandleCallbackCommand, InitiateOAuthCommand, OAuthProviderAdapter
from ..domain.repositories import OAuthConnectionRepository, OAuthStateRepository
from ..domain.services import EncryptionService
from .schemas import CallbackRequest, ConnectRequest, ConnectResponse


def create_auth_router(
    oauth_adapters: dict[str, OAuthProviderAdapter],
    state_repo: OAuthStateRepository,
    connection_repo: OAuthConnectionRepository,
    encryption_service: EncryptionService,
    event_bus: EventBus,
) -> APIRouter:
    router = APIRouter(tags=["auth"])

    @router.post("/connect", response_model=ConnectResponse)
    async def initiate_connect(req: ConnectRequest) -> ConnectResponse:
        adapter = oauth_adapters.get(req.provider)
        if adapter is None:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {req.provider}")

        cmd = InitiateOAuthCommand(
            oauth_provider_adapter=adapter,
            state_repo=state_repo,
        )
        # TODO: get user_id from JWT in real implementation
        result = await cmd.execute(
            provider=req.provider,
            user_id=uuid.uuid4(),
            redirect_uri=req.redirect_uri,
        )
        return ConnectResponse(authorize_url=result.authorize_url, state=result.state)

    @router.post("/callback")
    async def handle_callback(req: CallbackRequest) -> dict[str, str]:
        # Determine provider from state
        cmd = HandleCallbackCommand(
            oauth_provider_adapter=list(oauth_adapters.values())[0],
            state_repo=state_repo,
            connection_repo=connection_repo,
            encryption_service=encryption_service,
            event_bus=event_bus,
        )
        try:
            await cmd.execute(code=req.code, state=req.state)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return {"status": "connected"}

    return router
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest domains/auth/tests/integration/test_api.py -v`
Expected: All 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add domains/auth/api/
git commit -m "feat(auth): add FastAPI OAuth connect/callback endpoints"
```

---

### Task 8: Both Domains — MCP Servers

**Files:**
- Create: `domains/identity/mcp/__init__.py`
- Create: `domains/identity/mcp/server.py`
- Create: `domains/auth/mcp/__init__.py`
- Create: `domains/auth/mcp/server.py`
- Test: `domains/identity/tests/unit/test_mcp_server.py`
- Test: `domains/auth/tests/unit/test_mcp_server.py`

- [ ] **Step 1: Write the failing test for identity MCP**

```python
# domains/identity/tests/unit/test_mcp_server.py
from domains.identity.mcp.server import create_identity_mcp_server


class TestIdentityMCPServer:
    def test_server_has_required_tools(self) -> None:
        server = create_identity_mcp_server(
            user_repo=None, event_bus=None, token_service=None  # type: ignore
        )
        required_tools = [
            "identity.register",
            "identity.login",
            "identity.verify_session",
            "health.check",
        ]
        for tool in required_tools:
            assert tool in server.registered_tools, f"Missing tool: {tool}"
```

- [ ] **Step 2: Write the failing test for auth MCP**

```python
# domains/auth/tests/unit/test_mcp_server.py
from domains.auth.mcp.server import create_auth_mcp_server


class TestAuthMCPServer:
    def test_server_has_required_tools(self) -> None:
        server = create_auth_mcp_server(
            oauth_adapters={},
            state_repo=None,
            connection_repo=None,
            encryption_service=None,
            event_bus=None,  # type: ignore
        )
        required_tools = [
            "auth.connect",
            "auth.get_token",
            "auth.status",
            "health.check",
        ]
        for tool in required_tools:
            assert tool in server.registered_tools, f"Missing tool: {tool}"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest domains/identity/tests/unit/test_mcp_server.py domains/auth/tests/unit/test_mcp_server.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Write identity MCP server**

```python
# domains/identity/mcp/__init__.py
"""Identity MCP server."""
```

```python
# domains/identity/mcp/server.py
from __future__ import annotations

from shared.domain.events import EventBus
from shared.mcp.server_base import DomainMCPServer

from ..domain.repositories import UserRepository
from ..domain.services import TokenService


def create_identity_mcp_server(
    user_repo: UserRepository,
    event_bus: EventBus,
    token_service: TokenService,
) -> DomainMCPServer:
    server = DomainMCPServer(name="identity", port=9080)

    @server.tool("identity.register")
    async def register(email: str, password: str) -> dict:
        from ..application.commands import RegisterUserCommand
        cmd = RegisterUserCommand(user_repo=user_repo, event_bus=event_bus, token_service=token_service)
        result = await cmd.execute(email=email, password=password)
        return {"access_token": result.access_token, "refresh_token": result.refresh_token}

    @server.tool("identity.login")
    async def login(email: str, password: str) -> dict:
        from ..application.commands import LoginUserCommand
        cmd = LoginUserCommand(user_repo=user_repo, event_bus=event_bus, token_service=token_service)
        result = await cmd.execute(email=email, password=password)
        return {"access_token": result.access_token, "refresh_token": result.refresh_token}

    @server.tool("identity.verify_session")
    async def verify_session(token: str) -> dict:
        payload = token_service.verify_token(token)
        return {"user_id": payload["sub"], "roles": payload.get("roles", [])}

    return server
```

- [ ] **Step 5: Write auth MCP server**

```python
# domains/auth/mcp/__init__.py
"""Auth MCP server."""
```

```python
# domains/auth/mcp/server.py
from __future__ import annotations

import uuid

from shared.domain.events import EventBus
from shared.mcp.server_base import DomainMCPServer

from ..application.commands import InitiateOAuthCommand, OAuthProviderAdapter
from ..application.queries import GetConnectionStatusQuery, GetTokenQuery
from ..domain.repositories import OAuthConnectionRepository, OAuthStateRepository
from ..domain.services import EncryptionService


def create_auth_mcp_server(
    oauth_adapters: dict[str, OAuthProviderAdapter],
    state_repo: OAuthStateRepository,
    connection_repo: OAuthConnectionRepository,
    encryption_service: EncryptionService,
    event_bus: EventBus,
) -> DomainMCPServer:
    server = DomainMCPServer(name="auth", port=9070)

    @server.tool("auth.connect")
    async def connect(provider: str, user_id: str, redirect_uri: str) -> dict:
        adapter = oauth_adapters.get(provider)
        if adapter is None:
            return {"error": f"Unknown provider: {provider}"}
        cmd = InitiateOAuthCommand(oauth_provider_adapter=adapter, state_repo=state_repo)
        result = await cmd.execute(
            provider=provider, user_id=uuid.UUID(user_id), redirect_uri=redirect_uri
        )
        return {"authorize_url": result.authorize_url, "state": result.state}

    @server.tool("auth.get_token")
    async def get_token(user_id: str, provider: str) -> dict:
        query = GetTokenQuery(
            connection_repo=connection_repo, encryption_service=encryption_service
        )
        token = await query.execute(user_id=uuid.UUID(user_id), provider=provider)
        return {"access_token": token}

    @server.tool("auth.status")
    async def status(user_id: str) -> dict:
        query = GetConnectionStatusQuery(connection_repo=connection_repo)
        statuses = await query.execute(user_id=uuid.UUID(user_id))
        return {"connections": [{"provider": s.provider, "connected": s.connected} for s in statuses]}

    return server
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `uv run pytest domains/identity/tests/unit/test_mcp_server.py domains/auth/tests/unit/test_mcp_server.py -v`
Expected: All tests PASS

- [ ] **Step 7: Commit**

```bash
git add domains/identity/mcp/ domains/auth/mcp/ domains/identity/tests/ domains/auth/tests/
git commit -m "feat(identity,auth): add MCP servers with tool registration"
```

---

### Task 9: Run Full Test Suite for Both Domains

**Files:** None (verification)

- [ ] **Step 1: Run all identity tests**

Run: `uv run pytest domains/identity/tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 2: Run all auth tests**

Run: `uv run pytest domains/auth/tests/ -v --tb=short`
Expected: All tests PASS

- [ ] **Step 3: Run lint on both domains**

Run: `uv run ruff check domains/identity/ domains/auth/`
Expected: No errors

- [ ] **Step 4: Fix any issues and commit**

```bash
git add -A
git commit -m "chore(identity,auth): fix lint and finalize domain tests"
```
