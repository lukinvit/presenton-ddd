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
