# Agent Ecosystem

Windows AI provides a minimal agent framework with lifecycle hooks and a hub
for managing them.

## Agent interface

Agents follow the `windows_ai.agents.Agent` protocol which defines four
lifecycle methods:

- `setup()` – prepare any resources
- `train(data)` – learn from data
- `execute(task)` – run a task
- `teardown()` – release resources

`DomainAgent` is a basic implementation that wires an agent to a module from
`domains/`.

## AgentHub

`apps.agenthub` exposes a FastAPI service with endpoints to register, train and
run agents. Agents are registered against a domain such as natural language
processing, audio or vision, enabling them to leverage the corresponding
functions from `domains/`.

Example requests:

```
POST /agents/demo?domain=nlp
POST /agents/demo/train {"data": "text"}
POST /agents/demo/run {"task": "hello"}
```

## Workflow composition

`gui.core` now supports drag-and-drop workflow builders through
`WorkflowPanel`. Panels can embed external tools like FlowTool or ChainFlow and
be opened within the GUI.
