from __future__ import annotations

class SimpleModel:
    """A minimal concrete model used for testing and default behavior."""

    def generate(self, prompt: str) -> str:
        """Return a deterministic response for a given prompt."""
        return f"Echo: {prompt}"
