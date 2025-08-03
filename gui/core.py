from __future__ import annotations

from typing import Protocol, List


class Model(Protocol):
    """Protocol for models used by GuiCore."""

    def generate(self, prompt: str) -> str:
        """Generate a response for a given prompt."""
        raise NotImplementedError


class GuiCore:
    """Minimal GUI core placeholder.

    This class simulates launching a GUI application and routing chat
    messages to a local model while keeping a simple log of events.
    """

    def __init__(self, model: Model):
        self.model = model
        self.launched = False
        self._logs: List[str] = []

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

    def get_logs(self) -> List[str]:
        """Return the collected logs."""

        return list(self._logs)
