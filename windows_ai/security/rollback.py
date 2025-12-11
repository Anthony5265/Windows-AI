"""Simple rollback hook management utilities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List

Hook = Callable[[], None]


@dataclass
class RollbackManager:
    """Register and execute rollback hooks."""

    hooks: List[Hook] = field(default_factory=list)

    def add(self, hook: Hook) -> None:
        """Register *hook* to be executed on rollback."""

        self.hooks.append(hook)

    def rollback(self) -> None:
        """Execute registered hooks in reverse order and clear them."""

        while self.hooks:
            hook = self.hooks.pop()
            try:
                hook()
            except Exception:
                pass
