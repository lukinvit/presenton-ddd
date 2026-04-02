import uuid
from datetime import UTC, datetime

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
        assert event.occurred_at.tzinfo == UTC


class TestEventBusProtocol:
    def test_event_bus_is_protocol(self) -> None:
        import typing

        assert typing.runtime_checkable

        class FakeEventBus:
            async def publish(self, event: DomainEvent) -> None:
                pass

            async def subscribe(self, event_type: str, handler: object) -> None:
                pass

        assert isinstance(FakeEventBus(), EventBus)
