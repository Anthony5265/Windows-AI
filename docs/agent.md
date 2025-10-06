# Agent Overview

This page summarizes the lightweight agent framework that ships with Windows AI.
It highlights the canonical Python interfaces, the default domain-driven agent,
and the AgentHub service that orchestrates them.

## Core module: `windows_ai/agents.py`

The `Agent` protocol expresses a four-step lifecycle:

1. `setup()` prepares any resources required by the agent instance.
2. `train(data)` optionally updates internal state using caller-provided data.
3. `execute(task)` runs the agent against an arbitrary payload and returns a
   result object. The payload shape is defined by the agent implementation.
4. `teardown()` releases resources and clears any cached state.

The protocol is intentionally untyped beyond `Any` so that the same interface
can support synchronous domain helpers, local pipelines, or RPC proxies without
extra wrappers.

## Default implementation: `DomainAgent`

`DomainAgent` lives next to the protocol in `windows_ai/agents.py`.  It delegates
the lifecycle to a "domain" module that exposes four callables:

- `input_processor(data)` – sanitize or normalize inbound payloads.
- `task_planner(processed)` – produce a structured plan describing the work to do.
- `executor(plan)` – run the plan and emit raw results.
- `result_aggregator(results)` – collapse executor output into the response shape.

The repository ships three reference domains under `domains/`: natural language
processing, audio processing, and computer vision.  They demonstrate the function
signatures that DomainAgent expects and act as stubs for future integrations with
local models or remote APIs.

To introduce a new capability you typically:

1. Add a domain module (for example `domains/my_domain.py`) that implements the
   four callables above.
2. Register the module in `apps/agenthub/main.py` by extending the
   `DOMAIN_MODULES` mapping.
3. Restart AgentHub so it picks up the new registration.

## AgentHub service

`apps/agenthub/main.py` exposes a FastAPI application that manages agent
instances in memory.  Key endpoints include:

- `POST /agents/{name}` with a `domain` query parameter to register a new agent
  backed by one of the `DOMAIN_MODULES` entries.
- `POST /agents/{name}/train` to forward arbitrary training data to the agent.
- `POST /agents/{name}/run` to execute a task through the agent and receive the
  aggregated response.
- `GET /health` for lightweight service monitoring.

AgentHub also includes a `/pipeline/sample` route that exercises downstream
services (Actions API and the model proxy) to verify connectivity from a single
call.

## Testing references

A few helpful tests demonstrate how the pieces fit together:

- `tests/test_agent_lifecycle.py` drives `DomainAgent` through the full lifecycle
  using the NLP domain module.
- `tests/test_agenthub.py` covers the FastAPI contract for registering, training,
  and running agents over HTTP.
- `tests/test_nlp_pipeline.py` documents the behaviour of the NLP domain helpers
  that DomainAgent consumes.

Keeping this document in sync with `docs/agents.md` ensures both contributors and
stakeholders have consistent references for the agent architecture.
