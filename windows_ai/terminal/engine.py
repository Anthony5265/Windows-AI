from __future__ import annotations

import shlex
import subprocess
from typing import List, Tuple


class TerminalEngine:
    """Simple terminal engine that executes shell commands."""

    def __init__(self):
        self.history: List[Tuple[str, str]] = []

    def run(self, command: str) -> str:
        """Run *command* in a subprocess and capture stdout."""

        if any(char in command for char in ["|", ">", "<"]):
            raise ValueError("Pipes and redirection are not allowed")

        completed = subprocess.run(
            shlex.split(command),
            shell=False,
            capture_output=True,
            text=True,
            check=False,
        )
        output = completed.stdout.strip()
        self.history.append((command, output))
        return output
