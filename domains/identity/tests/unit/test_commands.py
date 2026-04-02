import uuid
import pytest
from unittest.mock import AsyncMock
from application.commands import RegisterUserCommand, LoginUserCommand
from application.dto import TokenPairDTO
from domain.entities import User
from domain.value_objects import Email, HashedPassword


class TestRegisterUserCommand:
    @pytest.mark.asyncio
    async def test_register_creates_user(self) -> None:
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=None)
        user_repo.save = AsyncMock()
        event_bus = AsyncMock()
        token_service = AsyncMock()
        token_service.create_access_token.return_value = "access_token"
        token_service.create_refresh_token.return_value = "refresh_token"
        cmd = RegisterUserCommand(user_repo=user_repo, event_bus=event_bus, token_service=token_service)
        result = await cmd.execute(email="new@example.com", password="secret123")
        assert isinstance(result, TokenPairDTO)
        assert result.access_token == "access_token"
        assert result.refresh_token == "refresh_token"
        user_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(self) -> None:
        existing = User(id=uuid.uuid4(), email=Email(value="exists@example.com"), password=HashedPassword.from_plain("pass"))
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=existing)
        cmd = RegisterUserCommand(user_repo=user_repo, event_bus=AsyncMock(), token_service=AsyncMock())
        with pytest.raises(ValueError, match="already registered"):
            await cmd.execute(email="exists@example.com", password="secret123")


class TestLoginUserCommand:
    @pytest.mark.asyncio
    async def test_login_success(self) -> None:
        user = User(id=uuid.uuid4(), email=Email(value="user@example.com"), password=HashedPassword.from_plain("correct_pass"), roles=[])
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=user)
        event_bus = AsyncMock()
        token_service = AsyncMock()
        token_service.create_access_token.return_value = "access"
        token_service.create_refresh_token.return_value = "refresh"
        cmd = LoginUserCommand(user_repo=user_repo, event_bus=event_bus, token_service=token_service)
        result = await cmd.execute(email="user@example.com", password="correct_pass")
        assert result.access_token == "access"

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises(self) -> None:
        user = User(id=uuid.uuid4(), email=Email(value="user@example.com"), password=HashedPassword.from_plain("correct_pass"))
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=user)
        cmd = LoginUserCommand(user_repo=user_repo, event_bus=AsyncMock(), token_service=AsyncMock())
        with pytest.raises(ValueError, match="Invalid credentials"):
            await cmd.execute(email="user@example.com", password="wrong_pass")

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_raises(self) -> None:
        user_repo = AsyncMock()
        user_repo.get_by_email = AsyncMock(return_value=None)
        cmd = LoginUserCommand(user_repo=user_repo, event_bus=AsyncMock(), token_service=AsyncMock())
        with pytest.raises(ValueError, match="Invalid credentials"):
            await cmd.execute(email="nobody@example.com", password="pass")
