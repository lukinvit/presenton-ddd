"""Content domain entities."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from shared.domain.entity import AggregateRoot, Entity

from .value_objects import OutlineItem


@dataclass
class ContentPlan(AggregateRoot):
    """Aggregate root for content planning — holds an ordered outline."""

    presentation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    topic: str = ""
    outline: list[OutlineItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_item(self, item: OutlineItem) -> None:
        self.outline.append(item)

    def replace_outline(self, items: list[OutlineItem]) -> None:
        self.outline = list(items)


@dataclass
class SlideContent(Entity):
    """Generated text content for a single slide."""

    plan_id: uuid.UUID = field(default_factory=uuid.uuid4)
    slide_index: int = 0
    title: str = ""
    body: str = ""
    speaker_notes: str = ""
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SystemPrompt(Entity):
    """A named, versioned system prompt template for LLM interactions."""

    name: str = ""
    prompt_text: str = ""
    variables: list[str] = field(default_factory=list)
    is_default: bool = False
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def update_text(self, prompt_text: str) -> None:
        self.prompt_text = prompt_text
        self.updated_at = datetime.now(UTC)

    def update_variables(self, variables: list[str]) -> None:
        self.variables = list(variables)
        self.updated_at = datetime.now(UTC)
