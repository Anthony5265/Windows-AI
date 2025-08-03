from __future__ import annotations

"""Utilities for syncing encrypted profile and model data to cloud providers."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Protocol
import hashlib
from itertools import cycle


class Provider(Protocol):
    """Abstract storage provider used by :class:`CloudSync`."""

    def upload(self, name: str, data: bytes) -> None:
        """Upload ``data`` under ``name``."""

    def download(self, name: str) -> bytes | None:
        """Retrieve data previously uploaded under ``name``."""


class InMemoryProvider:
    """Simple in-memory provider used for testing."""

    def __init__(self) -> None:
        self.storage: Dict[str, bytes] = {}

    def upload(self, name: str, data: bytes) -> None:  # pragma: no cover - tiny
        self.storage[name] = data

    def download(self, name: str) -> bytes | None:  # pragma: no cover - tiny
        return self.storage.get(name)


def _xor(data: bytes, key: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, cycle(key)))


def encrypt(data: bytes, password: str) -> bytes:
    """Encrypt ``data`` with ``password`` using a simple XOR scheme."""

    key = hashlib.sha256(password.encode()).digest()
    return _xor(data, key)


def decrypt(data: bytes, password: str) -> bytes:
    """Decrypt ``data`` with ``password``."""

    return encrypt(data, password)


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
    "CloudSync",
    "encrypt",
    "decrypt",
]
