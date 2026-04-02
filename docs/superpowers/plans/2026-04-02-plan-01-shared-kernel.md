# Plan 1: Shared Kernel + Infrastructure

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the shared kernel — base classes, event bus, MCP abstractions, DB config, logging, and project scaffolding that all 10 domains depend on.

**Architecture:** Shared kernel as a Python package (`shared/`) installed as editable dependency by each domain. Provides Protocol-based abstractions for EventBus, MCPTransport, and DatabaseConfig with two implementations each: production (Redis/PostgreSQL/TCP) and embedded (in-memory/SQLite/stdio). All domains import from `shared` — no cross-domain imports.

**Tech Stack:** Python 3.11, FastAPI, SQLModel, Redis (streams), PostgreSQL 16, structlog, FastMCP, pytest, ruff, mypy

---

## File Structure

```
presenton/
├── shared/
│   ├── pyproject.toml                      # Package definition
│   ├── shared/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entity.py                   # Base Entity, AggregateRoot
│   │   │   ├── value_object.py             # Base ValueObject
│   │   │   ├── events.py                   # DomainEvent base + EventBus protocol
│   │   │   └── repository.py               # Repository protocol
│   │   ├── infrastructure/
│   │   │   ├── __init__.py
│   │   │   ├── redis_event_bus.py          # Redis Streams EventBus
│   │   │   ├── in_memory_event_bus.py      # In-memory EventBus (Electron)
│   │   │   ├── database.py                 # DB engine factory, pool config
│   │   │   ├── logging.py                  # structlog setup
│   │   │   └── config.py                   # Settings from env
│   │   └── mcp/
│   │       ├── __init__.py
│   │       ├── server_base.py              # Base MCP server class
│   │       └── client.py                   # MCP client for calling other domains
│   └── tests/
│       ├── __init__.py
│       ├── test_entity.py
│       ├── test_value_object.py
│       ├── test_events.py
│       ├── test_redis_event_bus.py
│       ├── test_in_memory_event_bus.py
│       ├── test_database.py
│       ├── test_logging.py
│       ├── test_mcp_server_base.py
│       └── test_mcp_client.py
├── pyproject.toml                          # Root workspace config
├── ruff.toml                               # Linting config
├── mypy.ini                                # Type checking config
└── .pre-commit-config.yaml                 # Pre-commit hooks
```

---

### Task 1: Project Scaffolding and Tooling

**Files:**
- Create: `pyproject.toml` (root workspace)
- Create: `ruff.toml`
- Create: `mypy.ini`
- Create: `.pre-commit-config.yaml`
- Create: `shared/pyproject.toml`
- Create: `shared/shared/__init__.py`

- [ ] **Step 1: Create root pyproject.toml**

```toml
[project]
name = "presenton"
version = "1.0.0"
description = "Open-source AI presentation generator — DDD + MCP architecture"
requires-python = ">=3.11,<3.13"

[tool.uv.workspace]
members = ["shared", "domains/*"]
```

- [ ] **Step 2: Create ruff.toml**

```toml
target-version = "py311"
line-length = 100

[lint]
select = ["E", "F", "W", "I", "UP", "B", "SIM", "RUF"]
ignore = ["E501"]

[lint.isort]
known-first-party = ["shared"]
```

- [ ] **Step 3: Create mypy.ini**

```ini
[mypy]
python_version = 3.11
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true

[mypy-redis.*]
ignore_missing_imports = True

[mypy-fastmcp.*]
ignore_missing_imports = True
```

- [ ] **Step 4: Create .pre-commit-config.yaml**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies: [types-redis]
```

- [ ] **Step 5: Create shared package**

```toml
# shared/pyproject.toml
[project]
name = "presenton-shared"
version = "0.1.0"
description = "Shared kernel for Presenton DDD domains"
requires-python = ">=3.11,<3.13"
dependencies = [
    "sqlmodel>=0.0.24",
    "structlog>=24.0.0",
    "redis>=6.0.0",
    "fastmcp>=2.11.0",
    "pydantic>=2.0.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "aiosqlite>=0.21.0",
    "asyncpg>=0.30.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["shared"]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "ruff>=0.8.0",
    "mypy>=1.13.0",
]
```

```python
# shared/shared/__init__.py
"""Presenton Shared Kernel — base classes and infrastructure abstractions."""
```

- [ ] **Step 6: Initialize uv workspace and install**

Run: `cd /Users/v.lukin/Nextcloud/lukinvit.tech/projects/LV_Presentation && uv sync`
Expected: Workspace resolves, shared package installed in editable mode.

- [ ] **Step 7: Commit**

```bash
git init
git add pyproject.toml ruff.toml mypy.ini .pre-commit-config.yaml shared/
git commit -m "chore: scaffold project with uv workspace, ruff, mypy, pre-commit"
```

---

### Task 2: Base Entity and AggregateRoot

**Files:**
- Create: `shared/shared/domain/__init__.py`
- Create: `shared/shared/domain/entity.py`
- Test: `shared/tests/test_entity.py`

- [ ] **Step 1: Write the failing test**

```python
# shared/tests/test_entity.py
import uuid
from shared.domain.entity import Entity, AggregateRoot


class TestEntity:
    def test_entity_has_id(self) -> None:
        entity = Entity(id=uuid.uuid4())
        assert entity.id is not None

    def test_entity_equality_by_id(self) -> None:
        eid = uuid.uuid4()
        e1 = Entity(id=eid)
        e2 = Entity(id=eid)
        assert e1 == e2

    def test_entity_inequality_different_id(self) -> None:
        e1 = Entity(id=uuid.uuid4())
        e2 = Entity(id=uuid.uuid4())
        assert e1 != e2

    def test_entity_hash(self) -> None:
        eid = uuid.uuid4()
        e1 = Entity(id=eid)
        e2 = Entity(id=eid)
        assert hash(e1) == hash(e2)


class TestAggregateRoot:
    def test_aggregate_root_is_entity(self) -> None:
        root = AggregateRoot(id=uuid.uuid4())
        assert isinstance(root, Entity)

    def test_aggregate_root_collects_events(self) -> None:
        from shared.domain.events import DomainEvent

        root = AggregateRoot(id=uuid.uuid4())
        event = DomainEvent(aggregate_id=root.id, event_type="TestEvent")
        root.add_event(event)
        assert len(root.pending_events) == 1
        assert root.pending_events[0] is event

    def test_aggregate_root_clears_events(self) -> None:
        from shared.domain.events import DomainEvent

        root = AggregateRoot(id=uuid.uuid4())
        root.add_event(DomainEvent(aggregate_id=root.id, event_type="TestEvent"))
        root.clear_events()
        assert len(root.pending_events) == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/v.lukin/Nextcloud/lukinvit.tech/projects/LV_Presentation && uv run pytest shared/tests/test_entity.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'shared.domain.entity'`

- [ ] **Step 3: Write minimal implementation**

```python
# shared/shared/domain/__init__.py
"""Domain layer base classes."""
```

```python
# shared/shared/domain/entity.py
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared.domain.events import DomainEvent


@dataclass
class Entity:
    id: uuid.UUID

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class AggregateRoot(Entity):
    _pending_events: list[DomainEvent] = field(default_factory=list, repr=False)

    @property
    def pending_events(self) -> list[DomainEvent]:
        return list(self._pending_events)

    def add_event(self, event: DomainEvent) -> None:
        self._pending_events.append(event)

    def clear_events(self) -> None:
        self._pending_events.clear()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest shared/tests/test_entity.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/shared/domain/ shared/tests/test_entity.py
git commit -m "feat(shared): add Entity and AggregateRoot base classes"
```

---

### Task 3: ValueObject Base

**Files:**
- Create: `shared/shared/domain/value_object.py`
- Test: `shared/tests/test_value_object.py`

- [ ] **Step 1: Write the failing test**

```python
# shared/tests/test_value_object.py
from dataclasses import dataclass
from shared.domain.value_object import ValueObject


@dataclass(frozen=True)
class Color(ValueObject):
    hex_code: str
    name: str


class TestValueObject:
    def test_value_objects_equal_by_value(self) -> None:
        c1 = Color(hex_code="#FF0000", name="Red")
        c2 = Color(hex_code="#FF0000", name="Red")
        assert c1 == c2

    def test_value_objects_not_equal_different_values(self) -> None:
        c1 = Color(hex_code="#FF0000", name="Red")
        c2 = Color(hex_code="#00FF00", name="Green")
        assert c1 != c2

    def test_value_object_is_immutable(self) -> None:
        c = Color(hex_code="#FF0000", name="Red")
        try:
            c.hex_code = "#00FF00"  # type: ignore[misc]
            assert False, "Should raise FrozenInstanceError"
        except AttributeError:
            pass

    def test_value_object_hashable(self) -> None:
        c1 = Color(hex_code="#FF0000", name="Red")
        c2 = Color(hex_code="#FF0000", name="Red")
        assert hash(c1) == hash(c2)
        assert len({c1, c2}) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest shared/tests/test_value_object.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# shared/shared/domain/value_object.py
from dataclasses import dataclass


@dataclass(frozen=True)
class ValueObject:
    """Base class for value objects. Subclasses must also use @dataclass(frozen=True)."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest shared/tests/test_value_object.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/shared/domain/value_object.py shared/tests/test_value_object.py
git commit -m "feat(shared): add ValueObject base class"
```

---

### Task 4: DomainEvent and EventBus Protocol

**Files:**
- Create: `shared/shared/domain/events.py`
- Test: `shared/tests/test_events.py`

- [ ] **Step 1: Write the failing test**

```python
# shared/tests/test_events.py
import uuid
from datetime import datetime, timezone
from shared.domain.events import DomainEvent, EventBus


class TestDomainEvent:
    def test_domain_event_has_required_fields(self) -> None:
        agg_id = uuid.uuid4()
        event = DomainEvent(aggregate_id=agg_id, event_type="PresentationCreated")
        assert event.aggregate_id == agg_id
        assert event.event_type == "PresentationCreated"
        assert isinstance(event.event_id, uuid.UUID)
        assert isinstance(event.occurred_at, datetime)

    def test_domain_event_payload(self) -> None:
        event = DomainEvent(
            aggregate_id=uuid.uuid4(),
            event_type="SlideAdded",
            payload={"slide_index": 0, "title": "Intro"},
        )
        assert event.payload["slide_index"] == 0
        assert event.payload["title"] == "Intro"

    def test_domain_event_default_payload_is_empty(self) -> None:
        event = DomainEvent(aggregate_id=uuid.uuid4(), event_type="Test")
        assert event.payload == {}

    def test_domain_event_occurred_at_is_utc(self) -> None:
        event = DomainEvent(aggregate_id=uuid.uuid4(), event_type="Test")
        assert event.occurred_at.tzinfo == timezone.utc


class TestEventBusProtocol:
    def test_event_bus_is_protocol(self) -> None:
        """EventBus should be a Protocol — not instantiable directly, but
        any class with publish/subscribe methods satisfies it."""
        import typing

        assert typing.runtime_checkable

        class FakeEventBus:
            async def publish(self, event: DomainEvent) -> None:
                pass

            async def subscribe(
                self, event_type: str, handler: object
            ) -> None:
                pass

        assert isinstance(FakeEventBus(), EventBus)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest shared/tests/test_events.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# shared/shared/domain/events.py
from __future__ import annotations

import uuid
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable


@dataclass
class DomainEvent:
    aggregate_id: uuid.UUID
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


@runtime_checkable
class EventBus(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...

    async def subscribe(self, event_type: str, handler: EventHandler) -> None: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest shared/tests/test_events.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/shared/domain/events.py shared/tests/test_events.py
git commit -m "feat(shared): add DomainEvent and EventBus protocol"
```

---

### Task 5: Repository Protocol

**Files:**
- Create: `shared/shared/domain/repository.py`
- Test: (covered by test_entity.py — repository is a simple Protocol, tested through domain integration)

- [ ] **Step 1: Write the failing test**

```python
# Append to shared/tests/test_entity.py
import uuid
from shared.domain.repository import Repository
from shared.domain.entity import Entity


class TestRepositoryProtocol:
    def test_repository_is_protocol(self) -> None:
        import typing

        class FakeRepo:
            async def get(self, id: uuid.UUID) -> Entity | None:
                return None

            async def save(self, entity: Entity) -> None:
                pass

            async def delete(self, id: uuid.UUID) -> None:
                pass

        assert isinstance(FakeRepo(), Repository)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest shared/tests/test_entity.py::TestRepositoryProtocol -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# shared/shared/domain/repository.py
from __future__ import annotations

import uuid
from typing import Protocol, TypeVar, runtime_checkable

from shared.domain.entity import Entity

T = TypeVar("T", bound=Entity)


@runtime_checkable
class Repository(Protocol[T]):
    async def get(self, id: uuid.UUID) -> T | None: ...

    async def save(self, entity: T) -> None: ...

    async def delete(self, id: uuid.UUID) -> None: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest shared/tests/test_entity.py::TestRepositoryProtocol -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add shared/shared/domain/repository.py shared/tests/test_entity.py
git commit -m "feat(shared): add Repository protocol"
```

---

### Task 6: InMemoryEventBus (Electron target)

**Files:**
- Create: `shared/shared/infrastructure/__init__.py`
- Create: `shared/shared/infrastructure/in_memory_event_bus.py`
- Test: `shared/tests/test_in_memory_event_bus.py`

- [ ] **Step 1: Write the failing test**

```python
# shared/tests/test_in_memory_event_bus.py
import uuid
import pytest
from shared.domain.events import DomainEvent, EventBus
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus


@pytest.fixture
def bus() -> InMemoryEventBus:
    return InMemoryEventBus()


class TestInMemoryEventBus:
    @pytest.mark.asyncio
    async def test_implements_event_bus_protocol(self, bus: InMemoryEventBus) -> None:
        assert isinstance(bus, EventBus)

    @pytest.mark.asyncio
    async def test_publish_triggers_subscriber(self, bus: InMemoryEventBus) -> None:
        received: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        await bus.subscribe("TestEvent", handler)
        event = DomainEvent(aggregate_id=uuid.uuid4(), event_type="TestEvent")
        await bus.publish(event)
        assert len(received) == 1
        assert received[0] is event

    @pytest.mark.asyncio
    async def test_publish_does_not_trigger_other_subscribers(
        self, bus: InMemoryEventBus
    ) -> None:
        received: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        await bus.subscribe("OtherEvent", handler)
        event = DomainEvent(aggregate_id=uuid.uuid4(), event_type="TestEvent")
        await bus.publish(event)
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_event(
        self, bus: InMemoryEventBus
    ) -> None:
        count = {"a": 0, "b": 0}

        async def handler_a(event: DomainEvent) -> None:
            count["a"] += 1

        async def handler_b(event: DomainEvent) -> None:
            count["b"] += 1

        await bus.subscribe("TestEvent", handler_a)
        await bus.subscribe("TestEvent", handler_b)
        await bus.publish(
            DomainEvent(aggregate_id=uuid.uuid4(), event_type="TestEvent")
        )
        assert count["a"] == 1
        assert count["b"] == 1

    @pytest.mark.asyncio
    async def test_publish_no_subscribers_does_not_raise(
        self, bus: InMemoryEventBus
    ) -> None:
        event = DomainEvent(aggregate_id=uuid.uuid4(), event_type="NoSub")
        await bus.publish(event)  # Should not raise
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest shared/tests/test_in_memory_event_bus.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# shared/shared/infrastructure/__init__.py
"""Infrastructure layer — adapters and implementations."""
```

```python
# shared/shared/infrastructure/in_memory_event_bus.py
from __future__ import annotations

import asyncio
from collections import defaultdict

from shared.domain.events import DomainEvent, EventHandler


class InMemoryEventBus:
    """In-memory event bus for Electron / single-process deployments."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._subscribers.get(event.event_type, [])
        if handlers:
            await asyncio.gather(*(h(event) for h in handlers))

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest shared/tests/test_in_memory_event_bus.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/shared/infrastructure/ shared/tests/test_in_memory_event_bus.py
git commit -m "feat(shared): add InMemoryEventBus for Electron deployments"
```

---

### Task 7: RedisEventBus (Docker target)

**Files:**
- Create: `shared/shared/infrastructure/redis_event_bus.py`
- Test: `shared/tests/test_redis_event_bus.py`

- [ ] **Step 1: Write the failing test**

```python
# shared/tests/test_redis_event_bus.py
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from shared.domain.events import DomainEvent, EventBus
from shared.infrastructure.redis_event_bus import RedisEventBus


class TestRedisEventBus:
    def test_implements_event_bus_protocol(self) -> None:
        bus = RedisEventBus(redis_url="redis://localhost:6379", consumer_group="test")
        assert isinstance(bus, EventBus)

    @pytest.mark.asyncio
    async def test_publish_serializes_event_to_redis(self) -> None:
        bus = RedisEventBus(redis_url="redis://localhost:6379", consumer_group="test")
        mock_redis = AsyncMock()
        bus._redis = mock_redis

        event = DomainEvent(
            aggregate_id=uuid.UUID("12345678-1234-1234-1234-123456789abc"),
            event_type="PresentationCreated",
            payload={"title": "Test"},
        )
        await bus.publish(event)

        mock_redis.xadd.assert_called_once()
        call_args = mock_redis.xadd.call_args
        stream_name = call_args[0][0]
        assert stream_name == "events:PresentationCreated"

    @pytest.mark.asyncio
    async def test_subscribe_registers_handler(self) -> None:
        bus = RedisEventBus(redis_url="redis://localhost:6379", consumer_group="test")

        async def handler(event: DomainEvent) -> None:
            pass

        await bus.subscribe("TestEvent", handler)
        assert "TestEvent" in bus._handlers
        assert handler in bus._handlers["TestEvent"]

    def test_serialize_event(self) -> None:
        bus = RedisEventBus(redis_url="redis://localhost:6379", consumer_group="test")
        event = DomainEvent(
            aggregate_id=uuid.UUID("12345678-1234-1234-1234-123456789abc"),
            event_type="TestEvent",
            payload={"key": "value"},
        )
        serialized = bus._serialize_event(event)
        assert serialized["event_type"] == "TestEvent"
        assert serialized["aggregate_id"] == "12345678-1234-1234-1234-123456789abc"
        assert "payload" in serialized

    def test_deserialize_event(self) -> None:
        bus = RedisEventBus(redis_url="redis://localhost:6379", consumer_group="test")
        data = {
            "event_id": str(uuid.uuid4()),
            "aggregate_id": "12345678-1234-1234-1234-123456789abc",
            "event_type": "TestEvent",
            "payload": '{"key": "value"}',
            "occurred_at": "2026-04-02T12:00:00+00:00",
        }
        event = bus._deserialize_event(data)
        assert event.event_type == "TestEvent"
        assert event.payload == {"key": "value"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest shared/tests/test_redis_event_bus.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# shared/shared/infrastructure/redis_event_bus.py
from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import datetime, timezone

import redis.asyncio as aioredis

from shared.domain.events import DomainEvent, EventHandler


class RedisEventBus:
    """Redis Streams-based event bus for Docker/production deployments."""

    def __init__(self, redis_url: str, consumer_group: str) -> None:
        self._redis_url = redis_url
        self._consumer_group = consumer_group
        self._redis: aioredis.Redis | None = None
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    async def connect(self) -> None:
        self._redis = aioredis.from_url(self._redis_url, decode_responses=True)

    async def publish(self, event: DomainEvent) -> None:
        if self._redis is None:
            await self.connect()
        assert self._redis is not None
        stream_name = f"events:{event.event_type}"
        await self._redis.xadd(stream_name, self._serialize_event(event))

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    def _serialize_event(self, event: DomainEvent) -> dict[str, str]:
        return {
            "event_id": str(event.event_id),
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type,
            "payload": json.dumps(event.payload),
            "occurred_at": event.occurred_at.isoformat(),
        }

    def _deserialize_event(self, data: dict[str, str]) -> DomainEvent:
        return DomainEvent(
            event_id=uuid.UUID(data["event_id"]),
            aggregate_id=uuid.UUID(data["aggregate_id"]),
            event_type=data["event_type"],
            payload=json.loads(data["payload"]),
            occurred_at=datetime.fromisoformat(data["occurred_at"]),
        )

    async def start_consuming(self, consumer_name: str) -> None:
        """Start consuming events from Redis Streams. Call in a background task."""
        if self._redis is None:
            await self.connect()
        assert self._redis is not None

        streams: dict[str, str] = {}
        for event_type in self._handlers:
            stream = f"events:{event_type}"
            try:
                await self._redis.xgroup_create(
                    stream, self._consumer_group, id="0", mkstream=True
                )
            except aioredis.ResponseError:
                pass  # Group already exists
            streams[stream] = ">"

        while True:
            results = await self._redis.xreadgroup(
                groupname=self._consumer_group,
                consumername=consumer_name,
                streams=streams,
                count=10,
                block=1000,
            )
            for stream_name, messages in results:
                for message_id, data in messages:
                    event = self._deserialize_event(data)
                    handlers = self._handlers.get(event.event_type, [])
                    for handler in handlers:
                        await handler(event)
                    await self._redis.xack(
                        stream_name, self._consumer_group, message_id
                    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest shared/tests/test_redis_event_bus.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/shared/infrastructure/redis_event_bus.py shared/tests/test_redis_event_bus.py
git commit -m "feat(shared): add RedisEventBus with Streams for Docker deployments"
```

---

### Task 8: Database Configuration

**Files:**
- Create: `shared/shared/infrastructure/database.py`
- Test: `shared/tests/test_database.py`

- [ ] **Step 1: Write the failing test**

```python
# shared/tests/test_database.py
import pytest
from shared.infrastructure.database import create_engine_from_config, DatabaseConfig


class TestDatabaseConfig:
    def test_default_sqlite_config(self) -> None:
        config = DatabaseConfig(url="sqlite+aiosqlite:///test.db")
        assert config.url == "sqlite+aiosqlite:///test.db"
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.pool_recycle == 3600

    def test_postgres_config(self) -> None:
        config = DatabaseConfig(
            url="postgresql+asyncpg://user:pass@localhost/db",
            pool_size=20,
            max_overflow=40,
        )
        assert config.pool_size == 20
        assert config.max_overflow == 40

    def test_schema_config(self) -> None:
        config = DatabaseConfig(
            url="postgresql+asyncpg://user:pass@localhost/db",
            schema="presentation",
        )
        assert config.schema == "presentation"


class TestCreateEngine:
    def test_creates_engine_for_sqlite(self) -> None:
        config = DatabaseConfig(url="sqlite+aiosqlite:///test.db")
        engine = create_engine_from_config(config)
        assert engine is not None
        assert str(engine.url) == "sqlite+aiosqlite:///test.db"

    def test_creates_engine_for_postgres(self) -> None:
        config = DatabaseConfig(
            url="postgresql+asyncpg://user:pass@localhost/presenton",
            schema="presentation",
        )
        engine = create_engine_from_config(config)
        assert engine is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest shared/tests/test_database.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# shared/shared/infrastructure/database.py
from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


@dataclass
class DatabaseConfig:
    url: str
    pool_size: int = 10
    max_overflow: int = 20
    pool_recycle: int = 3600
    schema: str | None = None


def create_engine_from_config(config: DatabaseConfig) -> AsyncEngine:
    """Create an async SQLAlchemy engine from config with proper pool settings."""
    is_sqlite = config.url.startswith("sqlite")

    connect_args: dict = {}
    kwargs: dict = {}

    if is_sqlite:
        connect_args["check_same_thread"] = False
    else:
        kwargs["pool_size"] = config.pool_size
        kwargs["max_overflow"] = config.max_overflow
        kwargs["pool_recycle"] = config.pool_recycle

    engine = create_async_engine(config.url, connect_args=connect_args, **kwargs)

    # Set schema search path for PostgreSQL
    if config.schema and not is_sqlite:

        @event.listens_for(engine.sync_engine, "connect")
        def set_search_path(dbapi_conn, connection_record):  # type: ignore[no-untyped-def]
            cursor = dbapi_conn.cursor()
            cursor.execute(f"SET search_path TO {config.schema}, public")
            cursor.close()

    return engine
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest shared/tests/test_database.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/shared/infrastructure/database.py shared/tests/test_database.py
git commit -m "feat(shared): add DatabaseConfig and engine factory with pool settings"
```

---

### Task 9: Structured Logging

**Files:**
- Create: `shared/shared/infrastructure/logging.py`
- Test: `shared/tests/test_logging.py`

- [ ] **Step 1: Write the failing test**

```python
# shared/tests/test_logging.py
import json
import structlog
from shared.infrastructure.logging import setup_logging, get_logger


class TestLogging:
    def test_setup_logging_configures_structlog(self) -> None:
        setup_logging(json_output=False)
        logger = structlog.get_logger()
        assert logger is not None

    def test_get_logger_returns_bound_logger(self) -> None:
        setup_logging(json_output=False)
        logger = get_logger("test_domain")
        assert logger is not None

    def test_get_logger_includes_domain(self, capsys) -> None:
        setup_logging(json_output=True)
        logger = get_logger("presentation")
        logger.info("test message", key="value")
        captured = capsys.readouterr()
        parsed = json.loads(captured.out.strip())
        assert parsed["domain"] == "presentation"
        assert parsed["event"] == "test message"
        assert parsed["key"] == "value"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest shared/tests/test_logging.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# shared/shared/infrastructure/logging.py
from __future__ import annotations

import structlog


def setup_logging(json_output: bool = True) -> None:
    """Configure structlog for the application.

    Args:
        json_output: If True, output JSON lines (Docker). If False, human-readable (dev).
    """
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def get_logger(domain: str) -> structlog.stdlib.BoundLogger:
    """Get a logger bound to a specific domain name."""
    return structlog.get_logger(domain=domain)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest shared/tests/test_logging.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/shared/infrastructure/logging.py shared/tests/test_logging.py
git commit -m "feat(shared): add structlog-based logging with JSON and console output"
```

---

### Task 10: Configuration from Environment

**Files:**
- Create: `shared/shared/infrastructure/config.py`
- Test: `shared/tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# shared/tests/test_config.py
import os
import pytest
from shared.infrastructure.config import Settings, get_settings


class TestSettings:
    def test_default_settings(self) -> None:
        settings = Settings()
        assert settings.environment == "development"
        assert settings.log_json is False
        assert settings.redis_url == "redis://localhost:6379"
        assert settings.database_url == "sqlite+aiosqlite:///presenton.db"

    def test_settings_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PRESENTON_ENV", "production")
        monkeypatch.setenv("PRESENTON_LOG_JSON", "true")
        monkeypatch.setenv("PRESENTON_REDIS_URL", "redis://redis:6379")
        monkeypatch.setenv("PRESENTON_DATABASE_URL", "postgresql+asyncpg://u:p@pg/db")
        monkeypatch.setenv("PRESENTON_ENCRYPTION_KEY", "supersecretkey32bytes000000000000")

        settings = Settings.from_env()
        assert settings.environment == "production"
        assert settings.log_json is True
        assert settings.redis_url == "redis://redis:6379"
        assert settings.database_url == "postgresql+asyncpg://u:p@pg/db"
        assert settings.encryption_key == "supersecretkey32bytes000000000000"

    def test_get_settings_returns_singleton(self) -> None:
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest shared/tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# shared/shared/infrastructure/config.py
from __future__ import annotations

import os
from dataclasses import dataclass

_settings_instance: Settings | None = None


@dataclass
class Settings:
    environment: str = "development"
    log_json: bool = False
    redis_url: str = "redis://localhost:6379"
    database_url: str = "sqlite+aiosqlite:///presenton.db"
    encryption_key: str = ""
    allowed_origins: str = "http://localhost:3000"
    jwt_secret: str = ""
    jwt_algorithm: str = "RS256"
    app_data_directory: str = "./app_data"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            environment=os.getenv("PRESENTON_ENV", "development"),
            log_json=os.getenv("PRESENTON_LOG_JSON", "false").lower() == "true",
            redis_url=os.getenv("PRESENTON_REDIS_URL", "redis://localhost:6379"),
            database_url=os.getenv(
                "PRESENTON_DATABASE_URL", "sqlite+aiosqlite:///presenton.db"
            ),
            encryption_key=os.getenv("PRESENTON_ENCRYPTION_KEY", ""),
            allowed_origins=os.getenv("PRESENTON_ALLOWED_ORIGINS", "http://localhost:3000"),
            jwt_secret=os.getenv("PRESENTON_JWT_SECRET", ""),
            jwt_algorithm=os.getenv("PRESENTON_JWT_ALGORITHM", "RS256"),
            app_data_directory=os.getenv("PRESENTON_APP_DATA_DIR", "./app_data"),
        )


def get_settings() -> Settings:
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings.from_env()
    return _settings_instance


def reset_settings() -> None:
    """Reset cached settings — use in tests only."""
    global _settings_instance
    _settings_instance = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest shared/tests/test_config.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/shared/infrastructure/config.py shared/tests/test_config.py
git commit -m "feat(shared): add Settings config from environment variables"
```

---

### Task 11: MCP Server Base Class

**Files:**
- Create: `shared/shared/mcp/__init__.py`
- Create: `shared/shared/mcp/server_base.py`
- Test: `shared/tests/test_mcp_server_base.py`

- [ ] **Step 1: Write the failing test**

```python
# shared/tests/test_mcp_server_base.py
import pytest
from shared.mcp.server_base import DomainMCPServer


class TestDomainMCPServer:
    def test_create_server_with_name(self) -> None:
        server = DomainMCPServer(name="presentation", port=9010)
        assert server.name == "presentation"
        assert server.port == 9010

    def test_server_has_mcp_app(self) -> None:
        server = DomainMCPServer(name="style", port=9020)
        assert server.mcp is not None

    def test_register_tool(self) -> None:
        server = DomainMCPServer(name="test", port=9999)

        @server.tool("test.echo")
        async def echo(message: str) -> str:
            return message

        # Tool should be registered in the MCP server
        assert "test.echo" in server.registered_tools

    def test_health_endpoint_registered(self) -> None:
        server = DomainMCPServer(name="test", port=9999)
        assert "health.check" in server.registered_tools
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest shared/tests/test_mcp_server_base.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# shared/shared/mcp/__init__.py
"""MCP (Model Context Protocol) base classes."""
```

```python
# shared/shared/mcp/server_base.py
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastmcp import FastMCP


class DomainMCPServer:
    """Base MCP server for a bounded context domain.

    Provides tool registration, health check, and standard startup.
    """

    def __init__(self, name: str, port: int) -> None:
        self.name = name
        self.port = port
        self.mcp = FastMCP(name=f"presenton-{name}")
        self.registered_tools: dict[str, Callable[..., Any]] = {}

        # Register default health tool
        self._register_health()

    def _register_health(self) -> None:
        @self.tool("health.check")
        async def health_check() -> dict[str, str]:
            return {"status": "ok", "domain": self.name}

    def tool(self, name: str) -> Callable[..., Any]:
        """Decorator to register an MCP tool."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.registered_tools[name] = func
            self.mcp.tool(name=name)(func)
            return func

        return decorator

    async def start(self) -> None:
        """Start the MCP server. Override transport in subclasses if needed."""
        await self.mcp.run_async(transport="sse", port=self.port)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest shared/tests/test_mcp_server_base.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/shared/mcp/ shared/tests/test_mcp_server_base.py
git commit -m "feat(shared): add DomainMCPServer base class with tool registration"
```

---

### Task 12: MCP Client

**Files:**
- Create: `shared/shared/mcp/client.py`
- Test: `shared/tests/test_mcp_client.py`

- [ ] **Step 1: Write the failing test**

```python
# shared/tests/test_mcp_client.py
import pytest
from unittest.mock import AsyncMock, patch
from shared.mcp.client import MCPClient, MCPToolCall


class TestMCPClient:
    def test_create_client(self) -> None:
        client = MCPClient(base_urls={
            "presentation": "http://localhost:9010",
            "style": "http://localhost:9020",
        })
        assert "presentation" in client.base_urls
        assert "style" in client.base_urls

    def test_resolve_domain_from_tool_name(self) -> None:
        client = MCPClient(base_urls={
            "presentation": "http://localhost:9010",
            "style": "http://localhost:9020",
        })
        assert client._resolve_domain("presentation.create") == "presentation"
        assert client._resolve_domain("style.extract_from_file") == "style"

    def test_resolve_domain_unknown_raises(self) -> None:
        client = MCPClient(base_urls={
            "presentation": "http://localhost:9010",
        })
        with pytest.raises(ValueError, match="Unknown domain"):
            client._resolve_domain("unknown.tool")


class TestMCPToolCall:
    def test_tool_call_dataclass(self) -> None:
        call = MCPToolCall(tool="presentation.create", arguments={"title": "Test"})
        assert call.tool == "presentation.create"
        assert call.arguments == {"title": "Test"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest shared/tests/test_mcp_client.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# shared/shared/mcp/client.py
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from fastmcp import Client as FastMCPClient


@dataclass
class MCPToolCall:
    tool: str
    arguments: dict[str, Any] = field(default_factory=dict)


class MCPClient:
    """Client for calling MCP tools across domains.

    Routes tool calls to the correct domain based on tool name prefix.
    """

    def __init__(self, base_urls: dict[str, str]) -> None:
        self.base_urls = base_urls

    def _resolve_domain(self, tool_name: str) -> str:
        domain = tool_name.split(".")[0]
        if domain not in self.base_urls:
            raise ValueError(f"Unknown domain for tool '{tool_name}': '{domain}'")
        return domain

    async def call(self, tool: str, **kwargs: Any) -> Any:
        """Call a single MCP tool on the appropriate domain."""
        domain = self._resolve_domain(tool)
        url = self.base_urls[domain]
        async with FastMCPClient(url) as client:
            return await client.call_tool(tool, kwargs)

    async def call_parallel(self, calls: list[MCPToolCall]) -> list[Any]:
        """Call multiple MCP tools in parallel across domains."""
        tasks = [self.call(c.tool, **c.arguments) for c in calls]
        return await asyncio.gather(*tasks)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest shared/tests/test_mcp_client.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add shared/shared/mcp/client.py shared/tests/test_mcp_client.py
git commit -m "feat(shared): add MCPClient with domain routing and parallel calls"
```

---

### Task 13: Run Full Test Suite and Lint

**Files:** None (verification only)

- [ ] **Step 1: Run all tests**

Run: `uv run pytest shared/tests/ -v --tb=short`
Expected: All tests PASS (approximately 31 tests)

- [ ] **Step 2: Run ruff lint**

Run: `uv run ruff check shared/`
Expected: No errors

- [ ] **Step 3: Run ruff format check**

Run: `uv run ruff format --check shared/`
Expected: All files formatted correctly (or format them: `uv run ruff format shared/`)

- [ ] **Step 4: Run mypy**

Run: `uv run mypy shared/shared/`
Expected: No errors (or minor issues to fix)

- [ ] **Step 5: Fix any issues found and commit**

```bash
git add -A
git commit -m "chore(shared): fix lint and type check issues"
```

---

### Task 14: Export Shared Kernel Public API

**Files:**
- Modify: `shared/shared/__init__.py`
- Modify: `shared/shared/domain/__init__.py`
- Modify: `shared/shared/infrastructure/__init__.py`
- Modify: `shared/shared/mcp/__init__.py`

- [ ] **Step 1: Update domain __init__ exports**

```python
# shared/shared/domain/__init__.py
"""Domain layer base classes."""
from shared.domain.entity import AggregateRoot, Entity
from shared.domain.events import DomainEvent, EventBus, EventHandler
from shared.domain.repository import Repository
from shared.domain.value_object import ValueObject

__all__ = [
    "AggregateRoot",
    "DomainEvent",
    "Entity",
    "EventBus",
    "EventHandler",
    "Repository",
    "ValueObject",
]
```

- [ ] **Step 2: Update infrastructure __init__ exports**

```python
# shared/shared/infrastructure/__init__.py
"""Infrastructure layer — adapters and implementations."""
from shared.infrastructure.config import Settings, get_settings, reset_settings
from shared.infrastructure.database import DatabaseConfig, create_engine_from_config
from shared.infrastructure.in_memory_event_bus import InMemoryEventBus
from shared.infrastructure.logging import get_logger, setup_logging
from shared.infrastructure.redis_event_bus import RedisEventBus

__all__ = [
    "DatabaseConfig",
    "InMemoryEventBus",
    "RedisEventBus",
    "Settings",
    "create_engine_from_config",
    "get_logger",
    "get_settings",
    "reset_settings",
    "setup_logging",
]
```

- [ ] **Step 3: Update mcp __init__ exports**

```python
# shared/shared/mcp/__init__.py
"""MCP (Model Context Protocol) base classes."""
from shared.mcp.client import MCPClient, MCPToolCall
from shared.mcp.server_base import DomainMCPServer

__all__ = [
    "DomainMCPServer",
    "MCPClient",
    "MCPToolCall",
]
```

- [ ] **Step 4: Update root __init__ exports**

```python
# shared/shared/__init__.py
"""Presenton Shared Kernel — base classes and infrastructure abstractions."""
from shared.domain import (
    AggregateRoot,
    DomainEvent,
    Entity,
    EventBus,
    EventHandler,
    Repository,
    ValueObject,
)
from shared.infrastructure import (
    DatabaseConfig,
    InMemoryEventBus,
    RedisEventBus,
    Settings,
    create_engine_from_config,
    get_logger,
    get_settings,
    setup_logging,
)
from shared.mcp import DomainMCPServer, MCPClient, MCPToolCall

__all__ = [
    "AggregateRoot",
    "DatabaseConfig",
    "DomainEvent",
    "DomainMCPServer",
    "Entity",
    "EventBus",
    "EventHandler",
    "InMemoryEventBus",
    "MCPClient",
    "MCPToolCall",
    "RedisEventBus",
    "Repository",
    "Settings",
    "ValueObject",
    "create_engine_from_config",
    "get_logger",
    "get_settings",
    "setup_logging",
]
```

- [ ] **Step 5: Run tests to verify exports work**

Run: `uv run pytest shared/tests/ -v`
Expected: All tests still PASS

- [ ] **Step 6: Commit**

```bash
git add shared/shared/__init__.py shared/shared/domain/__init__.py shared/shared/infrastructure/__init__.py shared/shared/mcp/__init__.py
git commit -m "feat(shared): export clean public API from all subpackages"
```
