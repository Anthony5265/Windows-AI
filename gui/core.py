from __future__ import annotations

from typing import Protocol, List, Dict, Callable, Optional

from search import SearchEngine


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
        self.search_engine: Optional[SearchEngine] = None
        self._search_actions: Dict[str, Callable[[], None]] = {}

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

    # ---- search integration -------------------------------------------------

    def enable_search(self, engine: SearchEngine) -> None:
        """Attach a search engine and prepare the search overlay."""

        self.search_engine = engine
        self.add_overlay("search", "")

    def search(self, query: str) -> List[str]:
        """Execute a query and display results in the search overlay."""

        if self.search_engine is None:
            return []
        results = self.search_engine.search(query)
        overlay = self.overlays.get("search")
        if overlay:
            overlay.content = "\n".join(results)
            overlay.show()
        return results

    def register_search_action(self, result_id: str, action: Callable[[], None]) -> None:
        """Link a search result to an executable action."""

        self._search_actions[result_id] = action

    def activate_search_result(self, result_id: str) -> bool:
        """Execute the action associated with a search result."""

        action = self._search_actions.get(result_id)
        if action is None:
            return False
        action()
        return True
