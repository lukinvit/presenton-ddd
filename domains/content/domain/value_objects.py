"""Content domain value objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.domain.value_object import ValueObject


@dataclass(frozen=True)
class OutlineItem(ValueObject):
    """An item in a content plan outline (value object — no identity)."""

    index: int
    title: str
    key_points: tuple[str, ...]
    suggested_layout: str

    def __hash__(self) -> int:
        return hash((self.index, self.title, self.key_points, self.suggested_layout))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, OutlineItem):
            return NotImplemented
        return (
            self.index == other.index
            and self.title == other.title
            and self.key_points == other.key_points
            and self.suggested_layout == other.suggested_layout
        )


@dataclass(frozen=True)
class PromptTemplate(ValueObject):
    """A renderable prompt template with variable substitution."""

    template: str
    variables: dict[str, str] = field(default_factory=dict)

    def render(self) -> str:
        """Replace {var} placeholders with values from variables dict."""
        result = self.template
        for key, value in self.variables.items():
            result = result.replace(f"{{{key}}}", value)
        return result

    def __hash__(self) -> int:
        return hash((self.template, tuple(sorted(self.variables.items()))))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PromptTemplate):
            return NotImplemented
        return self.template == other.template and self.variables == other.variables
