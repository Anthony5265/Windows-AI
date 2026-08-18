"""Compatibility agent interfaces for Windows-AI.

The canonical runtime lives in :mod:`windows_ai.agent_runtime`. This module
keeps the older domain-agent protocol available for integrations that still
use it without introducing a second application-level agent registry.
"""

from __future__ import annotations

from typing import Any, Protocol


class Agent(Protocol):
    """Minimal lifecycle contract for legacy/domain integrations."""

    def setup(self) -> None: ...

    def train(self, data: Any) -> Any: ...

    def execute(self, task: Any) -> Any: ...

    def teardown(self) -> None: ...


class DomainAgent:
    """Adapter around a domain module's planning/execution functions."""

    def __init__(self, domain: Any) -> None:
        self.domain = domain
        self._trained_plan: Any | None = None

    def setup(self) -> None:
        """Prepare the domain adapter when the domain exposes setup."""
        setup = getattr(self.domain, "setup", None)
        if callable(setup):
            setup()

    def train(self, data: Any) -> Any:
        processed = self.domain.input_processor(data)
        self._trained_plan = self.domain.task_planner(processed)
        return self._trained_plan

    def execute(self, task: Any) -> Any:
        processed = self.domain.input_processor(task)
        plan = self.domain.task_planner(processed)
        results = self.domain.executor(plan)
        return self.domain.result_aggregator(results)

    def teardown(self) -> None:
        self._trained_plan = None
        teardown = getattr(self.domain, "teardown", None)
        if callable(teardown):
            teardown()
