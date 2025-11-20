"""Simple secure messaging protocol using XOR with HMAC.

This implementation provides lightweight encryption suitable for local
communications. It is **not** intended for production-grade security but
ensures messages are not transmitted in plain text and include integrity
checks.
"""

from __future__ import annotations

import hmac
import os
import hashlib

__all__ = ["SecureProtocol"]


class SecureProtocol:
    """Symmetric encryption and authentication helper."""

    def __init__(self, key: bytes | None = None) -> None:
        self.key = key or os.urandom(32)

    # ------------------------------------------------------------------ helpers
    def encrypt(self, message: bytes) -> bytes:
        """Encrypt *message* returning bytes with a MAC.

        A random nonce is generated for each message and repeated as a keystream
        using XOR. A SHA256 HMAC provides integrity checking.
        """

        nonce = os.urandom(16)
        cipher = bytes(m ^ nonce[i % len(nonce)] for i, m in enumerate(message))
        mac = hmac.new(self.key, nonce + cipher, hashlib.sha256).digest()
        return nonce + cipher + mac

    def decrypt(self, payload: bytes) -> bytes:
        """Verify and decrypt *payload* returning the original message."""

        nonce = payload[:16]
        mac = payload[-32:]
        cipher = payload[16:-32]
        expected = hmac.new(self.key, nonce + cipher, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected):
            raise ValueError("message authentication failed")
        message = bytes(c ^ nonce[i % len(nonce)] for i, c in enumerate(cipher))
        return message
