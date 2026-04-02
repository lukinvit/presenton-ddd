from dataclasses import dataclass


@dataclass(frozen=True)
class ValueObject:
    """Base class for value objects. Subclasses must also use @dataclass(frozen=True)."""

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.__dict__.items())))
