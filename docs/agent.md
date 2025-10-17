# Agent Overview

This guide summarizes the agent framework shipped with Windows AI and links to
the concrete implementations in the repository.  Use it as the canonical map
when extending agents, adding new domains, or wiring integrations into the
AgentHub service.

## Core protocol: `windows_ai/agents.py`

The `Agent` protocol defines a four-stage lifecycle implemented throughout the
codebase:

1. `setup()` prepares any resources required by the agent instance.
2. `train(data)` optionally updates internal state using caller-provided data and
   returns any intermediate artefacts the caller might need (for example a plan
   stub or statistics).
3. `execute(task)` runs the agent against an arbitrary payload and returns a
   result object.  Payload and result schemas are intentionally untyped so each
   domain can tailor them.
4. `teardown()` releases resources and clears cached state.

The protocol only relies on `typing.Protocol` to keep it lightweight—no abstract
base classes or mixins are required to build a compliant agent.

## Default implementation: `DomainAgent`

`DomainAgent` resides in the same module and delegates the lifecycle to a domain
module passed to its constructor.  The domain is expected to expose four
callables:

- `input_processor(data)` – normalize inbound payloads before planning.
- `task_planner(processed)` – produce an execution plan that downstream stages
  can consume.
- `executor(plan)` – perform the planned work and yield raw results.
- `result_aggregator(results)` – merge executor output into the public response.

`DomainAgent.train()` simply pipes data through the input processor and planner
and returns the resulting plan.  Tests exercise this behaviour with short NLP
strings that yield `{ "plan": [] }`, which callers can use to confirm the agent
initialized correctly.  `DomainAgent.execute()` intentionally recomputes the
plan for every call rather than reusing `_trained_plan`, keeping the flow
stateless outside the optional training hook.

## Built-in domains (`domains/`)

Three reference domains demonstrate the contract that `DomainAgent` expects:

- **Natural language processing** (`domains/natural_language_processing.py`)
  - Tokenizes text by lowercasing and splitting on whitespace.
  - Chooses between `local` and `remote` execution based on token count.
  - Returns results prefixed with `LOCAL:` or `REMOTE:` depending on the chosen
    route.  See `tests/test_nlp_pipeline.py` for end-to-end coverage.
- **Audio processing** (`domains/audio_processing.py`)
  - Marks audio samples longer than `REMOTE_THRESHOLD = 5.0` seconds for remote
    transcription; shorter samples stay on device.
  - Aggregates per-step transcripts into a single string while tracking the
    origin (`local` or `remote`).  Verified in `tests/test_audio_processing.py`.
- **Computer vision** (`domains/computer_vision.py`)
  - Normalizes images to RGB `(224, 224)` tensors.
  - Adds a remote classification step for dark images and performs local
    analysis otherwise, exercising both code paths in
    `tests/test_computer_vision.py`.

These modules are intentionally lightweight but provide a precise template for
adding new domains: mirror the four helper functions, add targeted tests, and
plug them into `AgentHub` (see below).

## Orchestration service: `apps/agenthub/main.py`

AgentHub exposes a FastAPI application that manages `Agent` instances in memory.
Key pieces include:

- `DOMAIN_MODULES` – maps public domain keys (`nlp`, `audio`, `vision`) to the
  domain helper modules.
- `AgentHub.register(name, domain_key)` – instantiates a `DomainAgent`, invokes
  `setup()`, and stores the instance.
- `AgentHub.train` / `AgentHub.run` – forward payloads to the underlying agent.
- Environment variables `ACTIONS_URL` and `PROXY_URL` – configure the optional
  `/pipeline/sample` diagnostic route that checks downstream Actions and model
  proxy services via asynchronous `httpx` calls.

HTTP endpoints mirror the registry methods (`POST /agents/{name}` with a `domain`
query string, `/agents/{name}/train`, `/agents/{name}/run`) plus health checks
and the pipeline sampler used throughout the tests in `tests/test_agenthub.py`.

## Tooling and GUI integration

The desktop GUI (`gui/core.py`) can embed external automation tools using
`WorkflowPanel`.  Tests currently register FlowTool panels via
`GuiCore.add_workflow_panel()` and open them through the GUI API.  Any
additional tooling should follow the same pattern; update `plugins/catalog.json`
if you want it to appear in the curated list of integrations.

## Validation checklist

The following tests exercise the agent stack and serve as regression references:

- `tests/test_agent_lifecycle.py` – drives AgentHub through registration,
  training, and execution using the NLP domain.
- `tests/test_agenthub.py` – verifies the FastAPI endpoints and the `/pipeline/sample`
  diagnostics, including error handling for downstream services.
- `tests/test_nlp_pipeline.py`, `tests/test_audio_processing.py`, and
  `tests/test_computer_vision.py` – cover each domain helper module directly.

Keep this document synchronized with the code and test suite so contributors can
quickly reason about the agent architecture and extend it safely.
