from __future__ import annotations


class SimpleModel:
    """Very small deterministic model used for tests and examples.

    It simply converts the prompt to upper case so responses are
    predictable in unit tests and demos.
    """

    def generate(self, prompt: str) -> str:
        """Return a deterministic response for *prompt*."""
        return prompt.upper()
