"""Core interfaces for building and training agents."""

from __future__ import annotations

from typing import Protocol, Any, Iterable


class Agent(Protocol):
    """Lifecycle hooks every agent should implement."""

    def setup(self) -> None:
        """Allocate resources required by the agent."""

    def train(self, data: Any) -> Any:
        """Train the agent using ``data`` and return training artefacts."""

    def execute(self, task: Any) -> Any:
        """Run ``task`` and return the result."""

    def teardown(self) -> None:
        """Release any resources held by the agent."""


class DomainAgent:
    """Minimal agent that delegates work to a domain module.

    The ``domain`` object must expose ``input_processor``, ``task_planner``,
    ``executor`` and ``result_aggregator`` callables.  The implementation is
    intentionally small so users can extend it for custom behaviour.
    """

    def __init__(self, domain: Any):
        self.domain = domain
        self._trained_plan: Any | None = None

    def setup(self) -> None:
        """Prepare the agent.  The base implementation is a no-op."""

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


class CollaborationProtocol(Protocol):
    """Strategy describing how multiple agents work together."""

    def coordinate(self, agents: Iterable[Agent], task: Any) -> Any:
        """Coordinate ``agents`` to accomplish ``task``."""


class Trainer(Protocol):
    """Interface for training an agent."""

    def train(self, agent: Agent, data: Any) -> Any:
        """Train ``agent`` with ``data`` and return training artefacts."""
