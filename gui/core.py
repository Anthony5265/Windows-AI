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


class WorkflowPanel:
    """Representation of an external workflow builder panel."""

    def __init__(self, tool: str, url: str):
        self.tool = tool
        self.url = url
        self.active = False

    def open(self) -> None:
        self.active = True

    def close(self) -> None:
        self.active = False


class Tooltip:
    """Simple tooltip representation bound to a UI element."""

    def __init__(self, target: str, text: str):
        self.target = target
        self.text = text
        self.visible = False

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False


class Walkthrough:
    """Sequential walkthrough composed of textual steps."""

    def __init__(self, steps: List[str]):
        self.steps = steps
        self._index = -1

    def start(self) -> Optional[str]:
        """Reset and return the first step."""
        self._index = -1
        return self.next_step()

    def next_step(self) -> Optional[str]:
        """Return the next step or None when finished."""
        self._index += 1
        if self._index < len(self.steps):
            return self.steps[self._index]
        return None


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
        self.tooltips: Dict[str, Tooltip] = {}
        self.walkthroughs: Dict[str, Walkthrough] = {}
        self.hotkeys = HotkeyManager()
        self.search_engine: Optional[SearchEngine] = None
        self._search_actions: Dict[str, Callable[[], None]] = {}
        self.workflow_panels: Dict[str, WorkflowPanel] = {}

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

    # ---- tooltips ---------------------------------------------------------

    def add_tooltip(self, target: str, text: str) -> Tooltip:
        """Create and register a tooltip for a UI element."""

        tip = Tooltip(target, text)
        self.tooltips[target] = tip
        return tip

    def show_tooltip(self, target: str) -> None:
        self.tooltips[target].show()

    def hide_tooltip(self, target: str) -> None:
        self.tooltips[target].hide()

    # ---- walkthroughs -----------------------------------------------------

    def add_walkthrough(self, name: str, steps: List[str]) -> Walkthrough:
        """Register a multi-step walkthrough sequence."""

        walk = Walkthrough(steps)
        self.walkthroughs[name] = walk
        return walk

    def start_walkthrough(self, name: str) -> Optional[str]:
        """Begin a walkthrough and return the first step."""

        walk = self.walkthroughs.get(name)
        if walk is None:
            return None
        return walk.start()

    def advance_walkthrough(self, name: str) -> Optional[str]:
        """Move to the next step in a walkthrough."""

        walk = self.walkthroughs.get(name)
        if walk is None:
            return None
        return walk.next_step()

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
