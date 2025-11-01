"""Spatial UI helpers with gesture and voice controls."""

from __future__ import annotations

from typing import Any, Dict

from ..input_manager import InputManager, Callback


class GestureVoiceController:
    """Route runtime events to an :class:`InputManager`."""

    def __init__(self, runtime: Any) -> None:
        self.runtime = runtime
        self.input = InputManager()

    def bind_gesture(self, name: str, callback: Callback) -> None:
        """Register a gesture callback."""

        self.input.register_gesture(name, callback)

    def bind_voice(self, phrase: str, callback: Callback) -> None:
        """Register a voice command callback."""

        self.input.register_voice_command(phrase, callback)

    def process_event(self, event: Dict[str, str]) -> bool:
        """Dispatch a gesture or voice event to the input manager.

        The event dictionary should contain a ``type`` key with value
        ``"gesture"`` or ``"voice"``. Gesture events should provide a
        ``name`` field while voice events should provide ``phrase``.
        """

        kind = event.get("type")
        if kind == "gesture":
            return self.input.handle_gesture(event.get("name", ""))
        if kind == "voice":
            return self.input.handle_voice_command(event.get("phrase", ""))
        return False


__all__ = ["GestureVoiceController"]
