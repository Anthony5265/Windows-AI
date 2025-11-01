from __future__ import annotations

"""Utilities for syncing encrypted profile and model data to cloud providers."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Protocol
import hashlib
import hmac
import os
from itertools import cycle


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
    """Store blobs on the local filesystem under ``root``."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def upload(self, name: str, data: bytes) -> None:  # pragma: no cover - tiny
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def download(self, name: str) -> bytes | None:  # pragma: no cover - tiny
        path = self.root / name
        return path.read_bytes() if path.exists() else None


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, cycle(key)))


def _derive_key(password: str) -> bytes:
    return hashlib.sha256(password.encode()).digest()


def encrypt(data: bytes, password: str) -> bytes:
    """Encrypt ``data`` with ``password`` using HMAC-authenticated XOR."""

    key = _derive_key(password)
    iv = os.urandom(16)
    keystream = hmac.new(key, iv, hashlib.sha256).digest()
    ciphertext = _xor(data, keystream)
    mac = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()
    return iv + mac + ciphertext


def decrypt(data: bytes, password: str) -> bytes:
    """Decrypt ``data`` with ``password`` verifying integrity."""

    key = _derive_key(password)
    iv = data[:16]
    mac = data[16:48]
    ciphertext = data[48:]
    expected = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(mac, expected):
        raise ValueError("integrity check failed")
    keystream = hmac.new(key, iv, hashlib.sha256).digest()
    return _xor(ciphertext, keystream)


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
