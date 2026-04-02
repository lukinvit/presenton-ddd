"""Shared test fixtures for gateway tests."""

from __future__ import annotations

import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# ---------------------------------------------------------------------------
# RSA key-pair generation (reused across all tests in the session)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def rsa_private_key():
    """Generate a fresh RSA-2048 private key for the test session."""
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(scope="session")
def private_key_pem(rsa_private_key) -> str:
    return rsa_private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


@pytest.fixture(scope="session")
def public_key_pem(rsa_private_key) -> str:
    return (
        rsa_private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )


# ---------------------------------------------------------------------------
# Token factory helpers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def make_token(private_key_pem):
    """Return a factory that mints a signed JWT."""

    def _factory(
        sub: str = "user-123",
        email: str = "test@example.com",
        roles: list[str] | None = None,
        exp_offset: int = 3600,
    ) -> str:
        payload = {
            "sub": sub,
            "email": email,
            "roles": roles or ["viewer"],
            "iat": int(time.time()),
            "exp": int(time.time()) + exp_offset,
        }
        return jwt.encode(payload, private_key_pem, algorithm="RS256")

    return _factory


@pytest.fixture(scope="session")
def valid_token(make_token) -> str:
    return make_token()


@pytest.fixture(scope="session")
def expired_token(make_token) -> str:
    return make_token(exp_offset=-10)
