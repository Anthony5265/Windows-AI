"""Agent interfaces and base implementations for Windows AI."""

from __future__ import annotations

from typing import Protocol, Any


class Agent(Protocol):
    """Protocol describing the lifecycle of an agent."""

    def setup(self) -> None:
        """Prepare resources needed by the agent."""

    def train(self, data: Any) -> Any:
        """Train the agent with ``data``."""

    def execute(self, task: Any) -> Any:
        """Execute ``task`` and return a result."""

    def teardown(self) -> None:
        """Release resources held by the agent."""


class DomainAgent:
    """Simple agent that delegates work to a domain module.

    The ``domain`` object is expected to expose the functions
    ``input_processor``, ``task_planner``, ``executor`` and
    ``result_aggregator``.  This mirrors the placeholder design used in
    :mod:`domains` modules and provides a minimal but functional example of
    how agents can leverage those capabilities.
    """

    def __init__(self, domain: Any):
        self.domain = domain
        self._trained_plan: Any | None = None

    # Lifecycle -------------------------------------------------------------
    def setup(self) -> None:
        """No-op setup for the basic agent."""

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
