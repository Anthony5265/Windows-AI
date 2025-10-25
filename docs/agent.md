# Agent Overview

This document provides a quick reference to the built-in agent framework that
powers Windows AI. Use it as the single-page summary when you need to orient
new contributors or vendors who only require the essentials.

## Core Protocol

All agents implement the `windows_ai.agents.Agent` protocol. The protocol
requires four lifecycle hooks, invoked in the following order:

1. `setup(config: Mapping[str, Any])` – allocate resources and validate the
   domain-specific configuration.
2. `train(data: Iterable[Any])` – optional hook that ingests labeled data.
3. `execute(payload: Mapping[str, Any]) -> AgentResult` – execute the agent's
   primary task and return a structured response.
4. `teardown()` – release any resources acquired during setup or execution.

The protocol is intentionally lightweight so that Python-based domains, CLI
integrations, or remote services can conform with minimal boilerplate.

## Default Implementation

`windows_ai.agents.domain_agent.DomainAgent` is the default implementation used
throughout the repository. It exposes a configuration contract that binds each
agent to a module under `domains/`. The DomainAgent bootstraps the module's
`Service` class and forwards lifecycle calls to the service instance.

To add a new agent you typically:

1. Create a new domain module in `domains/<your_domain>/`.
2. Implement a `Service` class with `setup`, `train`, `execute`, and `teardown`
   methods (mirroring the agent protocol).
3. Register the domain inside `windows_ai/agents/registry.py` so the hub can
   discover it.

## Agent Hub

The FastAPI application in `apps/agenthub` manages the full agent lifecycle. It
provides REST endpoints to register, configure, train, and execute agents.
When a client triggers an execution request, the hub loads the configured agent
class, injects secrets or credentials from the secure store, and returns the
normalized `AgentResult` payload.

The hub also exposes health and telemetry endpoints that stream task-level
metrics for observability dashboards such as Azure Monitor or Grafana.

## GUI Integration

The React-based GUI under `ui/` surfaces a **Workflow Panel** that lets users
compose multi-step automations. Agents appear as draggable tiles, and the panel
connects them with conditional routing, allowing results from one agent to feed
another. Advanced users can embed external tools (e.g., FlowTool or ChainFlow)
by pointing the panel at third-party manifest URLs.

## Testing & Tooling

* `tests/agents/test_domain_agent.py` exercises the protocol compliance for the
  default agent implementation.
* `tests/apps/agenthub` contains integration tests for the REST API contract.
* `scripts/agents/scaffold.py` can scaffold new domain skeletons from the CLI.

Keeping this document updated alongside `docs/agents.md` ensures newcomers have
both the short-form and in-depth references they need.
