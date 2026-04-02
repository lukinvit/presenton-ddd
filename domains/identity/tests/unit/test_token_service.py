import uuid
import pytest
from datetime import timedelta
from domain.services import TokenService


class TestTokenService:
    def setup_method(self) -> None:
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.private_pem = private_key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
        ).decode()
        self.public_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        self.service = TokenService(private_key=self.private_pem, public_key=self.public_pem, algorithm="RS256")

    def test_create_access_token(self) -> None:
        user_id = uuid.uuid4()
        token = self.service.create_access_token(user_id=user_id, roles=["editor"])
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token(self) -> None:
        user_id = uuid.uuid4()
        token = self.service.create_access_token(user_id=user_id, roles=["editor"])
        payload = self.service.verify_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["roles"] == ["editor"]
        assert payload["type"] == "access"

    def test_create_refresh_token(self) -> None:
        user_id = uuid.uuid4()
        token = self.service.create_refresh_token(user_id=user_id)
        payload = self.service.verify_token(token)
        assert payload["type"] == "refresh"

    def test_expired_token_raises(self) -> None:
        user_id = uuid.uuid4()
        token = self.service.create_access_token(user_id=user_id, roles=[], ttl=timedelta(seconds=-1))
        with pytest.raises(Exception):
            self.service.verify_token(token)

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(Exception):
            self.service.verify_token("invalid.token.here")
