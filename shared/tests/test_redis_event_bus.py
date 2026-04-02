import uuid
from unittest.mock import AsyncMock

import pytest

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
