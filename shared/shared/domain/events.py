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
