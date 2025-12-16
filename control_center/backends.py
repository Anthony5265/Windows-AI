"""Language model backend implementations for the Control Center."""

from __future__ import annotations

from dataclasses import dataclass, field
from secrets import token_urlsafe
from typing import Dict, List, Protocol, Tuple

__all__ = [
    "Backend",
        "ChainBackend",
    "LocalBackend",
    "RemoteBackend",
    "Session",
    "SessionManager",
    "load_backend",
    "set_context_menu",
    "context_menu_enabled",
]


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

class ChainBackend:
    """Chain multiple backends sequentially.
    
    The output of each backend becomes the input to the next backend,
    allowing for multi-stage processing of prompts.
    
    Examples
    --------
    >>> local = LocalBackend()
    >>> remote = RemoteBackend()
    >>> chain = ChainBackend([local, remote])
    >>> chain.generate("hi")
    '[remote] [local] hi'
    """
    
    def __init__(self, backends: List[Backend]):
        """Initialize with a list of backends to chain.
        
        Parameters
        ----------
        backends : List[Backend]
            Backends to chain in order. Each backend's output becomes
            the next backend's input.
        """
        self.backends = backends
    
    def generate(self, prompt: str) -> str:
        """Generate by passing through each backend sequentially.
        
        Parameters
        ----------
        prompt : str
            Initial prompt to process.
            
        Returns
        -------
        str
            Final output after passing through all backends in sequence.
        """
        result = prompt
        for backend in self.backends:
            result = backend.generate(result)
        return result


_context_menu_enabled = False


# ---------------------------------------------------------------- Session API
@dataclass
class Session:
    """Represent an interactive session for a specific user and backend."""

    user: str
    backend: Backend
    history: List[Tuple[str, str]] = field(default_factory=list)


class SessionManager:
    """Manage multiple user sessions for different backends."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Session] = {}

    # --------------------------------------------------------------- lifecycle
    def create(self, user: str, backend: Backend) -> str:
        """Create a new session and return its id."""

        sid = token_urlsafe(16)
        self._sessions[sid] = Session(user, backend)
        return sid

    def end(self, session_id: str) -> None:
        """Terminate a session if it exists."""

        self._sessions.pop(session_id, None)

    # ----------------------------------------------------------------- helpers
    def get(self, session_id: str) -> Session:
        return self._sessions[session_id]

    def send(self, session_id: str, prompt: str) -> str:
        """Send *prompt* through the session's backend and record the result."""

        session = self.get(session_id)
        response = session.backend.generate(prompt)
        session.history.append((prompt, response))
        return response


def set_context_menu(enabled: bool) -> None:
    """Enable or disable context menu integration."""

    global _context_menu_enabled
    _context_menu_enabled = bool(enabled)


def context_menu_enabled() -> bool:
    """Return whether the context menu integration is enabled."""

    return _context_menu_enabled


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
