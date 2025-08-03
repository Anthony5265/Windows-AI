from __future__ import annotations

from typing import Protocol, List, Dict, Callable


class Model(Protocol):
    """Protocol for models used by GuiCore."""

    def generate(self, prompt: str) -> str:
        """Generate a response for a given prompt."""
        raise NotImplementedError


class OverlayWidget:
    """Very small representation of an overlay widget."""

    def __init__(self, name: str, content: str):
        self.name = name
        self.content = content
        self.visible = False

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False


class HotkeyManager:
    """Register and trigger hotkey callbacks."""

    def __init__(self):
        self._handlers: Dict[str, Callable[[], None]] = {}

    def register(self, combo: str, handler: Callable[[], None]) -> None:
        self._handlers[combo] = handler

    def trigger(self, combo: str) -> bool:
        handler = self._handlers.get(combo)
        if handler is None:
            return False
        handler()
        return True


class GuiCore:
    """Minimal GUI core placeholder with overlays and hotkeys."""

    def __init__(self, model: Model):
        self.model = model
        self.launched = False
        self._logs: List[str] = []
        self.overlays: Dict[str, OverlayWidget] = {}
        self.hotkeys = HotkeyManager()

    def launch(self) -> bool:
        """Launch the GUI and record the event.

        Returns True if the launch sequence completes.
        """

        self.launched = True
        self._logs.append("GUI launched")
        return True

    def chat(self, message: str) -> str:
        """Send a message to the model and log the interaction."""

        response = self.model.generate(message)
        self._logs.append(f"chat: {message}")
        return response

    def add_overlay(self, name: str, content: str) -> OverlayWidget:
        """Create and store an overlay widget."""

        widget = OverlayWidget(name, content)
        self.overlays[name] = widget
        return widget

    def show_overlay(self, name: str) -> None:
        self.overlays[name].show()

    def hide_overlay(self, name: str) -> None:
        self.overlays[name].hide()

    def register_hotkey(self, combo: str, handler: Callable[[], None]) -> None:
        self.hotkeys.register(combo, handler)

    def handle_hotkey(self, combo: str) -> bool:
        """Trigger a registered hotkey."""

        return self.hotkeys.trigger(combo)

    def get_logs(self) -> List[str]:
        """Return the collected logs."""

        return list(self._logs)
