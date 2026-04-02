from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from shared.domain.value_object import ValueObject


class OAuthProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    CUSTOM = "custom"


@dataclass(frozen=True)
class EncryptedToken(ValueObject):
    value: str
