"""Backend abstractions for local and remote language models.

This module provides a small interface for LLM backends and helpers to
construct local, remote or chained backends.  The classes here are extremely
light‑weight stubs used for testing; real implementations would wrap actual
model APIs.
"""
from __future__ import annotations

from typing import Iterable, Protocol

__all__ = [
    "Backend",
    "LocalBackend",
    "RemoteBackend",
    "ChainBackend",
    "load_backend",
]


class Backend(Protocol):
    """Minimal interface required by the chat UI."""

    def generate(self, prompt: str) -> str:
        """Return a textual response for *prompt*."""


class LocalBackend:
    """Simple stub representing an on-device model."""

    def generate(self, prompt: str) -> str:  # pragma: no cover - trivial
        return f"[local] {prompt}"


class RemoteBackend:
    """Stub representing a remote/cloud model."""

    def generate(self, prompt: str) -> str:  # pragma: no cover - trivial
        return f"[remote] {prompt}"


class ChainBackend:
    """Backend that feeds the response of one backend into the next."""

    def __init__(self, backends: Iterable[Backend]):
        self.backends = list(backends)

    def generate(self, prompt: str) -> str:
        response = prompt
        for backend in self.backends:
            response = backend.generate(response)
        return response


def load_backend(kind: str) -> Backend:
    """Return a backend instance for *kind*.

    Parameters
    ----------
    kind:
        Either ``"local"`` or ``"remote"``.
    """

    kind = kind.lower()
    if kind == "local":
        return LocalBackend()
    if kind == "remote":
        return RemoteBackend()
    raise ValueError(f"unknown backend: {kind}")
