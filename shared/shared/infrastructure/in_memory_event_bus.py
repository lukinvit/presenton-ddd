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
