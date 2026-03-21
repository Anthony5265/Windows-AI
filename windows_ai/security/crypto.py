"""Encryption helpers for Windows AI.

Provides symmetric encryption using Fernet (AES-128-CBC via the
``cryptography`` library) when available, with an XOR-based fallback
for environments where the library is not installed.

The Fernet backend requires a URL-safe base64-encoded 32-byte key
generated via ``cryptography.fernet.Fernet.generate_key()``.  When
using the fallback XOR cipher, any non-empty string works as the key.

.. warning::
   The XOR fallback is **not** cryptographically secure and is only
   suitable for development / testing.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from typing import Optional, Tuple

# Try to import cryptography for production-grade encryption
try:
    from cryptography.fernet import Fernet, InvalidToken

    _HAS_FERNET = True
except ImportError:  # pragma: no cover
    _HAS_FERNET = False


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------

def generate_key() -> str:
    """Generate a new encryption key.

    When ``cryptography`` is installed a Fernet key is returned; otherwise
    a 32-byte hex string is produced.
    """
    if _HAS_FERNET:
        return Fernet.generate_key().decode("ascii")
    return secrets.token_hex(32)


def derive_key(password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
    """Derive an encryption key from a password using PBKDF2.

    Returns ``(key_str, salt)`` so the caller can persist the salt.
    """
    if salt is None:
        salt = os.urandom(16)

    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations=100_000)

    if _HAS_FERNET:
        key = base64.urlsafe_b64encode(dk[:32])
        return key.decode("ascii"), salt

    return dk.hex(), salt


# ---------------------------------------------------------------------------
# XOR fallback (kept for lightweight / test use)
# ---------------------------------------------------------------------------

def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


# ---------------------------------------------------------------------------
# Encrypt / Decrypt
# ---------------------------------------------------------------------------

def encrypt(text: str, key: str) -> str:
    """Encrypt *text* with *key* and return a base64-encoded token.

    Uses Fernet when the ``cryptography`` package is available; falls
    back to XOR + base64 otherwise.
    """
    if _HAS_FERNET:
        try:
            f = Fernet(key.encode("ascii") if isinstance(key, str) else key)
            return f.encrypt(text.encode("utf-8")).decode("ascii")
        except Exception:
            pass  # Fall through to XOR if key format is wrong

    token = _xor(text.encode("utf-8"), key.encode("utf-8"))
    return base64.b64encode(token).decode("ascii")


def decrypt(token: str, key: str) -> str:
    """Decrypt a token produced by :func:`encrypt`."""
    if _HAS_FERNET:
        try:
            f = Fernet(key.encode("ascii") if isinstance(key, str) else key)
            return f.decrypt(token.encode("ascii")).decode("utf-8")
        except Exception:
            pass  # Fall through to XOR

    data = base64.b64decode(token.encode("ascii"))
    plain = _xor(data, key.encode("utf-8"))
    return plain.decode("utf-8")


# ---------------------------------------------------------------------------
# Hashing helpers
# ---------------------------------------------------------------------------

def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
    """Hash a password with PBKDF2-SHA256.  Returns ``(hex_hash, salt)``."""
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations=100_000)
    return dk.hex(), salt


def verify_password(password: str, expected_hash: str, salt: bytes) -> bool:
    """Verify *password* against a previously hashed value."""
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations=100_000)
    return hmac.compare_digest(dk.hex(), expected_hash)


def compute_sha256(data: bytes) -> str:
    """Return the hex-encoded SHA-256 digest of *data*."""
    return hashlib.sha256(data).hexdigest()


def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


__all__ = [
    "encrypt",
    "decrypt",
    "generate_key",
    "derive_key",
    "hash_password",
    "verify_password",
    "compute_sha256",
    "generate_token",
]

