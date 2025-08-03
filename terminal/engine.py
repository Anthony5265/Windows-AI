from __future__ import annotations

import subprocess
from typing import List, Tuple


class TerminalEngine:
    """Simple terminal engine that executes shell commands."""

    def __init__(self):
        self.history: List[Tuple[str, str]] = []

    def run(self, command: str) -> str:
        """Run *command* in a subprocess and capture stdout."""

        completed = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=False
        )
        output = completed.stdout.strip()
        self.history.append((command, output))
        return output
