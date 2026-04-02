import uuid
from datetime import UTC, datetime, timedelta

from domains.identity.domain.entities import Role, Session, User
from domains.identity.domain.value_objects import Email, HashedPassword, Permission


class TestEmail:
    def test_valid_email(self) -> None:
        email = Email(value="user@example.com")
        assert email.value == "user@example.com"

    def test_email_equality(self) -> None:
        e1 = Email(value="user@example.com")
        e2 = Email(value="user@example.com")
        assert e1 == e2

    def test_email_case_insensitive(self) -> None:
        e1 = Email(value="User@Example.COM")
        assert e1.value == "user@example.com"


class TestHashedPassword:
    def test_create_from_plain(self) -> None:
        hp = HashedPassword.from_plain("securepassword123")
        assert hp.hash_value != "securepassword123"
        assert hp.hash_value.startswith("$2b$")

    def test_verify_correct_password(self) -> None:
        hp = HashedPassword.from_plain("securepassword123")
        assert hp.verify("securepassword123") is True

    def test_verify_wrong_password(self) -> None:
        hp = HashedPassword.from_plain("securepassword123")
        assert hp.verify("wrongpassword") is False


class TestRole:
    def test_role_has_permissions(self) -> None:
        role = Role(
            id=uuid.uuid4(),
            name="editor",
            permissions=[
                Permission(resource="presentation", action="read"),
                Permission(resource="presentation", action="write"),
            ],
        )
        assert len(role.permissions) == 2

    def test_role_has_permission(self) -> None:
        role = Role(
            id=uuid.uuid4(),
            name="editor",
            permissions=[Permission(resource="presentation", action="read")],
        )
        assert role.has_permission("presentation", "read") is True
        assert role.has_permission("presentation", "delete") is False


class TestUser:
    def test_create_user(self) -> None:
        user = User(
            id=uuid.uuid4(),
            email=Email(value="test@example.com"),
            password=HashedPassword.from_plain("pass123"),
            roles=[],
        )
        assert user.email.value == "test@example.com"

    def test_user_has_role(self) -> None:
        role = Role(id=uuid.uuid4(), name="admin", permissions=[])
        user = User(
            id=uuid.uuid4(),
            email=Email(value="admin@example.com"),
            password=HashedPassword.from_plain("pass"),
            roles=[role],
        )
        assert user.has_role("admin") is True
        assert user.has_role("viewer") is False


class TestSession:
    def test_session_not_expired(self) -> None:
        session = Session(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        assert session.is_expired is False

    def test_session_expired(self) -> None:
        session = Session(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        )
        assert session.is_expired is True
