from __future__ import annotations
import json
import uuid
from collections import defaultdict
from datetime import datetime
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
        if self._redis is None:
            await self.connect()
        assert self._redis is not None
        streams: dict[str, str] = {}
        for event_type in self._handlers:
            stream = f"events:{event_type}"
            try:
                await self._redis.xgroup_create(stream, self._consumer_group, id="0", mkstream=True)
            except aioredis.ResponseError:
                pass
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
                    await self._redis.xack(stream_name, self._consumer_group, message_id)
