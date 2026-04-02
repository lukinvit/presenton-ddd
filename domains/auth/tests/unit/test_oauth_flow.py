import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from domains.auth.application.commands import HandleCallbackCommand, InitiateOAuthCommand
from domains.auth.application.dto import OAuthURLDTO
from domains.auth.domain.entities import OAuthConnection
from domains.auth.domain.value_objects import EncryptedToken, OAuthProvider


class TestOAuthProvider:
    def test_anthropic_provider(self) -> None:
        provider = OAuthProvider.ANTHROPIC
        assert provider.value == "anthropic"

    def test_openai_provider(self) -> None:
        provider = OAuthProvider.OPENAI
        assert provider.value == "openai"

    def test_gemini_provider(self) -> None:
        provider = OAuthProvider.GEMINI
        assert provider.value == "gemini"


class TestOAuthConnection:
    def test_create_connection(self) -> None:
        conn = OAuthConnection(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            provider=OAuthProvider.ANTHROPIC,
            access_token=EncryptedToken(value="encrypted_access"),
            refresh_token=EncryptedToken(value="encrypted_refresh"),
            expires_at=None,
        )
        assert conn.provider == OAuthProvider.ANTHROPIC

    def test_is_expired_none_means_no_expiry(self) -> None:
        conn = OAuthConnection(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            provider=OAuthProvider.GEMINI,
            access_token=EncryptedToken(value="enc"),
            refresh_token=None,
            expires_at=None,
        )
        assert conn.is_expired(buffer_seconds=300) is False


class TestInitiateOAuthCommand:
    @pytest.mark.asyncio
    async def test_generates_authorize_url(self) -> None:
        oauth_provider_adapter = AsyncMock()
        oauth_provider_adapter.get_authorize_url.return_value = (
            "https://console.anthropic.com/oauth/authorize?client_id=xxx&state=abc",
            "abc",
            "verifier123",
        )
        state_repo = AsyncMock()
        cmd = InitiateOAuthCommand(
            oauth_provider_adapter=oauth_provider_adapter, state_repo=state_repo
        )
        result = await cmd.execute(
            provider="anthropic",
            user_id=uuid.uuid4(),
            redirect_uri="http://localhost:5000/api/v1/auth/callback",
        )
        assert isinstance(result, OAuthURLDTO)
        assert "anthropic.com" in result.authorize_url
        state_repo.save.assert_called_once()


class TestHandleCallbackCommand:
    @pytest.mark.asyncio
    async def test_exchanges_code_for_tokens(self) -> None:
        oauth_provider_adapter = AsyncMock()
        oauth_provider_adapter.exchange_code.return_value = {
            "access_token": "raw_access",
            "refresh_token": "raw_refresh",
            "expires_in": 3600,
        }
        state_repo = AsyncMock()
        state_repo.get_and_delete.return_value = {
            "provider": "anthropic",
            "user_id": str(uuid.uuid4()),
            "code_verifier": "verifier123",
        }
        connection_repo = AsyncMock()
        encryption_service = MagicMock()
        encryption_service.encrypt.side_effect = lambda x: f"enc_{x}"
        event_bus = AsyncMock()
        cmd = HandleCallbackCommand(
            oauth_provider_adapter=oauth_provider_adapter,
            state_repo=state_repo,
            connection_repo=connection_repo,
            encryption_service=encryption_service,
            event_bus=event_bus,
        )
        await cmd.execute(code="auth_code_123", state="abc")
        connection_repo.save.assert_called_once()
        saved = connection_repo.save.call_args[0][0]
        assert isinstance(saved, OAuthConnection)
        assert saved.access_token.value == "enc_raw_access"
