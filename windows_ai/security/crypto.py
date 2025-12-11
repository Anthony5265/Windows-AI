"""Lightweight encryption helpers.

These helpers use a very small XOR cipher combined with base64 encoding.
They are **not** meant for production use but serve to illustrate how
encryption utilities could be structured.
"""

from __future__ import annotations

import base64


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt(text: str, key: str) -> str:
    """Encrypt ``text`` using ``key`` and return a base64 token."""

    token = _xor(text.encode("utf-8"), key.encode("utf-8"))
    return base64.b64encode(token).decode("ascii")


def decrypt(token: str, key: str) -> str:
    """Decrypt a base64 token produced by :func:`encrypt`."""

    data = base64.b64decode(token.encode("ascii"))
    plain = _xor(data, key.encode("utf-8"))
    return plain.decode("utf-8")


__all__ = ["encrypt", "decrypt"]
