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
    async def test_publish_does_not_trigger_other_subscribers(self, bus: InMemoryEventBus) -> None:
        received: list[DomainEvent] = []
        async def handler(event: DomainEvent) -> None:
            received.append(event)
        await bus.subscribe("OtherEvent", handler)
        event = DomainEvent(aggregate_id=uuid.uuid4(), event_type="TestEvent")
        await bus.publish(event)
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_multiple_subscribers_same_event(self, bus: InMemoryEventBus) -> None:
        count = {"a": 0, "b": 0}
        async def handler_a(event: DomainEvent) -> None:
            count["a"] += 1
        async def handler_b(event: DomainEvent) -> None:
            count["b"] += 1
        await bus.subscribe("TestEvent", handler_a)
        await bus.subscribe("TestEvent", handler_b)
        await bus.publish(DomainEvent(aggregate_id=uuid.uuid4(), event_type="TestEvent"))
        assert count["a"] == 1
        assert count["b"] == 1

    @pytest.mark.asyncio
    async def test_publish_no_subscribers_does_not_raise(self, bus: InMemoryEventBus) -> None:
        event = DomainEvent(aggregate_id=uuid.uuid4(), event_type="NoSub")
        await bus.publish(event)
