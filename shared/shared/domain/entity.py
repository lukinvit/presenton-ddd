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
