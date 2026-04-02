from __future__ import annotations
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    """AES-256-GCM encryption for token storage."""
    NONCE_SIZE = 12

    def __init__(self, key: str) -> None:
        key_bytes = key.encode("utf-8")[:32].ljust(32, b"\0")
        self._aesgcm = AESGCM(key_bytes)

    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(self.NONCE_SIZE)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def decrypt(self, encrypted: str) -> str:
        raw = base64.b64decode(encrypted.encode("utf-8"))
        nonce = raw[:self.NONCE_SIZE]
        ciphertext = raw[self.NONCE_SIZE:]
        plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
