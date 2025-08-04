"""Gesture and voice input handling for XR environments."""

from __future__ import annotations

from typing import Callable, Dict

Callback = Callable[[], None]


class InputManager:
    """Map gestures and voice commands to callbacks.

    The manager stores simple mappings and invokes the registered callbacks
    when an input is handled.  Unknown inputs are ignored and ``False`` is
    returned so callers can fall back to other handling mechanisms.
    """

    def __init__(self) -> None:
        self._gestures: Dict[str, Callback] = {}
        self._voice: Dict[str, Callback] = {}

    def register_gesture(self, name: str, callback: Callback) -> None:
        """Associate ``name`` with ``callback`` for gesture events."""

        self._gestures[name] = callback

    def register_voice_command(self, phrase: str, callback: Callback) -> None:
        """Associate ``phrase`` with ``callback`` for voice events."""

        self._voice[phrase.lower()] = callback

    def handle_gesture(self, name: str) -> bool:
        """Invoke the callback mapped to ``name`` if present."""

        cb = self._gestures.get(name)
        if cb:
            cb()
            return True
        return False

    def handle_voice_command(self, phrase: str) -> bool:
        """Invoke the callback mapped to ``phrase`` if present."""

        cb = self._voice.get(phrase.lower())
        if cb:
            cb()
            return True
        return False


__all__ = ["InputManager"]
