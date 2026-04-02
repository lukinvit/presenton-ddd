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
