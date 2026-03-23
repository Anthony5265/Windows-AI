"""Rollback management utilities for Windows AI.

Provides safe rollback of operations via hook registration, checkpoint
snapshots, and transactional grouping. Used to undo partial changes when
multi-step operations fail midway.
"""

from __future__ import annotations

import copy
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

Hook = Callable[[], None]


@dataclass
class RollbackCheckpoint:
    """Snapshot of state at a specific point in time."""
    name: str
    state: Dict[str, Any]
    created_at: float = field(default_factory=time.time)


class RollbackManager:
    """Register and execute rollback hooks with checkpoint support.

    Features
    --------
    * **Hook registration** – add undo functions that execute in reverse order.
    * **Checkpoints** – snapshot arbitrary state dicts for point-in-time restore.
    * **Transactions** – group operations; rollback the group on failure.
    * **History** – track which rollbacks have been executed.
    """

    def __init__(self) -> None:
        self.hooks: List[Hook] = []
        self._checkpoints: List[RollbackCheckpoint] = []
        self._history: List[Dict[str, Any]] = []
        self._transaction_stack: List[int] = []

    # ------------------------------------------------------------------
    # Hook management
    # ------------------------------------------------------------------

    def add(self, hook: Hook) -> None:
        """Register *hook* to be executed on rollback."""
        self.hooks.append(hook)

    def rollback(self) -> int:
        """Execute registered hooks in reverse order and clear them.

        Returns the number of hooks executed.
        """
        executed = 0
        errors: List[str] = []

        while self.hooks:
            hook = self.hooks.pop()
            try:
                hook()
                executed += 1
            except Exception as exc:
                errors.append(str(exc))
                logger.warning("Rollback hook failed: %s", exc)

        self._history.append({
            "action": "rollback",
            "hooks_executed": executed,
            "errors": errors,
            "timestamp": time.time(),
        })
        return executed

    # ------------------------------------------------------------------
    # Checkpoints
    # ------------------------------------------------------------------

    def create_checkpoint(self, name: str, state: Dict[str, Any]) -> RollbackCheckpoint:
        """Create a checkpoint by deep-copying *state*."""
        cp = RollbackCheckpoint(name=name, state=copy.deepcopy(state))
        self._checkpoints.append(cp)
        logger.info("Checkpoint created: %s", name)
        return cp

    def restore_checkpoint(self, name: str) -> Optional[Dict[str, Any]]:
        """Return the state dict saved under *name*, or ``None``."""
        for cp in reversed(self._checkpoints):
            if cp.name == name:
                self._history.append({
                    "action": "restore_checkpoint",
                    "name": name,
                    "timestamp": time.time(),
                })
                return copy.deepcopy(cp.state)
        return None

    def list_checkpoints(self) -> List[str]:
        """Return names of all stored checkpoints."""
        return [cp.name for cp in self._checkpoints]

    def delete_checkpoint(self, name: str) -> bool:
        """Delete a checkpoint by name. Returns True if found."""
        for i, cp in enumerate(self._checkpoints):
            if cp.name == name:
                self._checkpoints.pop(i)
                return True
        return False

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    def begin_transaction(self) -> None:
        """Mark the start of a transaction.

        All hooks added after this call belong to the current transaction.
        On ``rollback_transaction`` only those hooks are undone.
        """
        self._transaction_stack.append(len(self.hooks))

    def commit_transaction(self) -> None:
        """Commit the current transaction (keep hooks, pop marker)."""
        if self._transaction_stack:
            self._transaction_stack.pop()

    def rollback_transaction(self) -> int:
        """Rollback the current transaction only.

        Returns the number of hooks executed.
        """
        if not self._transaction_stack:
            return self.rollback()

        marker = self._transaction_stack.pop()
        executed = 0
        errors: List[str] = []

        while len(self.hooks) > marker:
            hook = self.hooks.pop()
            try:
                hook()
                executed += 1
            except Exception as exc:
                errors.append(str(exc))
                logger.warning("Transaction rollback hook failed: %s", exc)

        self._history.append({
            "action": "rollback_transaction",
            "hooks_executed": executed,
            "errors": errors,
            "timestamp": time.time(),
        })
        return executed

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def pending_hooks(self) -> int:
        """Number of registered rollback hooks."""
        return len(self.hooks)

    @property
    def history(self) -> List[Dict[str, Any]]:
        """Log of rollback actions."""
        return list(self._history)

    def clear(self) -> None:
        """Clear all hooks, checkpoints, and history."""
        self.hooks.clear()
        self._checkpoints.clear()
        self._transaction_stack.clear()

