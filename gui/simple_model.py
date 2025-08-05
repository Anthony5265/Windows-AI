from __future__ import annotations

class SimpleModel:
    """Very small model used for tests and examples."""

    def generate(self, prompt: str) -> str:
        """Return a deterministic response for *prompt*."""
        return prompt.upper()
