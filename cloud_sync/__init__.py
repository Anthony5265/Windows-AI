from __future__ import annotations

"""Utilities for syncing encrypted profile and model data to cloud providers."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Protocol
import hashlib
import hmac
import os



class Provider(Protocol):
    """Abstract storage provider used by :class:`CloudSync`."""

    def upload(self, name: str, data: bytes) -> None:
        """Upload ``data`` under ``name``."""

    def download(self, name: str) -> bytes | None:
        """Retrieve data previously uploaded under ``name``."""


class InMemoryProvider:
    """Simple in-memory provider used for testing."""

    def __init__(self) -> None:  # pragma: no cover - tiny
        self.storage: Dict[str, bytes] = {}

    def upload(self, name: str, data: bytes) -> None:  # pragma: no cover - tiny
        self.storage[name] = data

    def download(self, name: str) -> bytes | None:  # pragma: no cover - tiny
        return self.storage.get(name)


class FilesystemProvider:
    """Store uploaded files on the local filesystem.

    ``name`` is treated as a file name relative to the base directory
    provided at construction time.  The base directory is created if it
    does not already exist.
    """

    def __init__(self, base: str | Path) -> None:
        self.base = Path(base)
        self.base.mkdir(parents=True, exist_ok=True)

    def _path(self, name: str) -> Path:
        return self.base / name

    def upload(self, name: str, data: bytes) -> None:  # pragma: no cover - tiny
        self._path(name).write_bytes(data)

    def download(self, name: str) -> bytes | None:  # pragma: no cover - tiny
        path = self._path(name)
        return path.read_bytes() if path.exists() else None


def _keystream(key: bytes, iv: bytes, length: int) -> bytes:
    """Generate a pseudo-random keystream using HMAC-SHA256."""

    stream = b""
    counter = 0
    while len(stream) < length:
        block = hmac.new(key, iv + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        stream += block
        counter += 1
    return stream[:length]


def encrypt(data: bytes, password: str) -> bytes:
    """Encrypt ``data`` with ``password`` using HMAC for confidentiality and integrity.

    The returned blob is ``IV || ciphertext || tag`` where ``tag`` is an HMAC
    over the IV and ciphertext.  A random 16-byte IV is used for each
    encryption.
    """

    key = hashlib.sha256(password.encode()).digest()
    iv = os.urandom(16)
    stream = _keystream(key, iv, len(data))
    ciphertext = bytes(a ^ b for a, b in zip(data, stream))
    tag = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()
    return iv + ciphertext + tag


def decrypt(data: bytes, password: str) -> bytes:
    """Decrypt ``data`` with ``password`` and verify integrity."""

    key = hashlib.sha256(password.encode()).digest()
    if len(data) < 16 + 32:
        raise ValueError("ciphertext too short")
    iv = data[:16]
    tag = data[-32:]
    ciphertext = data[16:-32]
    expected = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(tag, expected):
        raise ValueError("HMAC verification failed")
    stream = _keystream(key, iv, len(ciphertext))
    return bytes(a ^ b for a, b in zip(ciphertext, stream))


@dataclass
class CloudSync:
    """High level interface for backing up files to a provider."""

    provider: Provider
    password: str
    conflict_resolution: str = "ask"

    def backup_file(self, path: str | Path, name: str) -> None:
        data = Path(path).read_bytes()
        enc = encrypt(data, self.password)
        self.provider.upload(name, enc)

    def restore_file(self, path: str | Path, name: str) -> bool:
        data = self.provider.download(name)
        if data is None:
            return False
        dec = decrypt(data, self.password)
        Path(path).write_bytes(dec)
        return True

    def sync_file(self, path: str | Path, name: str) -> str:
        """Synchronise ``path`` with remote ``name``.

        Returns a string describing the action taken:
        ``"uploaded"``, ``"downloaded"``, ``"noop`` or raises ``RuntimeError``
        if a conflict occurs and ``conflict_resolution`` is ``"ask"``.
        """

        local_path = Path(path)
        local_bytes = local_path.read_bytes() if local_path.exists() else None
        remote_enc = self.provider.download(name)
        remote_bytes = (
            decrypt(remote_enc, self.password) if remote_enc is not None else None
        )

        if remote_bytes is None and local_bytes is not None:
            self.provider.upload(name, encrypt(local_bytes, self.password))
            return "uploaded"

        if remote_bytes is not None and local_bytes is None:
            local_path.write_bytes(remote_bytes)
            return "downloaded"

        if remote_bytes is None and local_bytes is None:
            return "noop"

        assert remote_bytes is not None and local_bytes is not None
        if remote_bytes == local_bytes:
            return "noop"

        if self.conflict_resolution == "local":
            self.provider.upload(name, encrypt(local_bytes, self.password))
            return "uploaded"
        if self.conflict_resolution == "remote":
            local_path.write_bytes(remote_bytes)
            return "downloaded"
        raise RuntimeError("sync conflict")


__all__ = [
    "Provider",
    "InMemoryProvider",
    "FilesystemProvider",
    "CloudSync",
    "encrypt",
    "decrypt",
]
