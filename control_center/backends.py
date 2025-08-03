"""Language model backend implementations for the Control Center."""

from __future__ import annotations

from typing import Protocol

__all__ = ["Backend", "LocalBackend", "RemoteBackend", "load_backend"]


class Backend(Protocol):
    """Minimal interface for language model backends."""

    def generate(self, prompt: str) -> str:
        """Return a textual response for *prompt*."""


class LocalBackend:
    """Very small stub implementation representing an on-device model."""

    def generate(self, prompt: str) -> str:  # pragma: no cover - trivial
        return f"[local] {prompt}"


class RemoteBackend:
    """Stub implementation representing a cloud model."""

    def generate(self, prompt: str) -> str:  # pragma: no cover - trivial
        return f"[remote] {prompt}"


def load_backend(kind: str) -> Backend:
    """Return a backend instance for *kind*.

    Parameters
    ----------
    kind: str
        Either ``"local"`` or ``"remote"``.
    """

    kind = kind.lower()
    if kind == "local":
        return LocalBackend()
    if kind == "remote":
        return RemoteBackend()
    raise ValueError(f"unknown backend: {kind}")
