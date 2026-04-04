"""In-memory store for encrypted API keys."""

from __future__ import annotations

from domains.auth.domain.services import EncryptionService

_SUPPORTED_PROVIDERS = ["anthropic", "openai", "google", "ollama"]


class InMemoryConnectionStore:
    """Stores encrypted API keys in memory (process-lifetime)."""

    def __init__(self, encryption_service: EncryptionService) -> None:
        self._connections: dict[str, str] = {}  # provider -> encrypted_key
        self._encryption = encryption_service

    def store_key(self, provider: str, api_key: str) -> None:
        self._connections[provider] = self._encryption.encrypt(api_key)

    def get_key(self, provider: str) -> str | None:
        encrypted = self._connections.get(provider)
        if encrypted:
            return self._encryption.decrypt(encrypted)
        return None

    def list_connections(self) -> list[dict]:
        return [
            {"provider": p, "connected": p in self._connections}
            for p in _SUPPORTED_PROVIDERS
        ]

    def disconnect(self, provider: str) -> None:
        self._connections.pop(provider, None)
