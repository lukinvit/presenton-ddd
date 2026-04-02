"""Shared InMemoryEventBus instance for all domains in Electron mode.

Import `shared_event_bus` wherever a domain needs an event bus.  Because all
domains run in the same Python process, a single bus instance is sufficient —
no Redis or TCP transport is needed.
"""

from __future__ import annotations

from shared.infrastructure.in_memory_event_bus import InMemoryEventBus

# Singleton event bus shared across all domains
shared_event_bus: InMemoryEventBus = InMemoryEventBus()
