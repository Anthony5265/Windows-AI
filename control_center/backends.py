"""Language model backend implementations for the Control Center."""

from __future__ import annotations

from typing import Protocol

__all__ = ["Backend", "LocalBackend", "RemoteBackend"]


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
