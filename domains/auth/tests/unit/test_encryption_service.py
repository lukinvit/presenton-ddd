import pytest
from cryptography.exceptions import InvalidTag

from domains.auth.domain.services import EncryptionService


class TestEncryptionService:
    def setup_method(self) -> None:
        self.key = "a" * 32
        self.service = EncryptionService(key=self.key)

    def test_encrypt_returns_different_from_plaintext(self) -> None:
        encrypted = self.service.encrypt("my_secret_token")
        assert encrypted != "my_secret_token"

    def test_decrypt_returns_original(self) -> None:
        original = "sk-ant-api03-xxxxx"
        encrypted = self.service.encrypt(original)
        decrypted = self.service.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_same_text_produces_different_ciphertexts(self) -> None:
        e1 = self.service.encrypt("same")
        e2 = self.service.encrypt("same")
        assert e1 != e2

    def test_decrypt_with_wrong_key_raises(self) -> None:
        encrypted = self.service.encrypt("secret")
        wrong_service = EncryptionService(key="b" * 32)
        with pytest.raises(InvalidTag):
            wrong_service.decrypt(encrypted)

    def test_encrypt_empty_string(self) -> None:
        encrypted = self.service.encrypt("")
        decrypted = self.service.decrypt(encrypted)
        assert decrypted == ""
