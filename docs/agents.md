# Agent Ecosystem

Windows AI provides a minimal agent framework with lifecycle hooks and a hub
for managing them.  The core interfaces live in the top-level :mod:`agents`
package so users can build custom implementations without depending on
``windows_ai`` internals.

## Agent interface

Agents follow the `agents.Agent` protocol which defines four
lifecycle methods:

- `setup()` – prepare any resources
- `train(data)` – learn from data
- `execute(task)` – run a task
- `teardown()` – release resources

`DomainAgent` is a basic implementation that wires an agent to a module from
`domains/`.

## AgentHub

`apps.agenthub` exposes a FastAPI service with endpoints to register, train,
list and remove agents. Agents are registered against a domain such as natural
language processing, audio or vision, enabling them to leverage the
corresponding functions from `domains/`. A `/marketplace` endpoint fetches
available agents from an external catalog.

Example requests:

```
POST /agents/demo?domain=nlp
POST /agents/demo/train {"data": "text"}
POST /agents/demo/run {"task": "hello"}
GET  /agents
DELETE /agents/demo
GET  /marketplace
```

## Workflow composition

`gui.core` now supports drag-and-drop workflow builders through
`WorkflowPanel`. Panels can embed external tools like FlowTool or ChainFlow and
be opened within the GUI.

## Workflow examples

### Custom agent

```python
from agents import Agent

class EchoAgent:
    def setup(self):
        pass

    def train(self, data):
        return data

    def execute(self, task):
        return task

    def teardown(self):
        pass
```

### Collaboration protocol

```python
from agents import CollaborationProtocol

class BroadcastProtocol(CollaborationProtocol):
    def coordinate(self, agents, task):
        return [agent.execute(task) for agent in agents]
```

### Training interface

```python
from agents import Trainer

class SimpleTrainer(Trainer):
    def train(self, agent, data):
        return agent.train(data)
```
