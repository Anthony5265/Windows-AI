import os
from typing import Dict, Any, Iterable
from fastapi import FastAPI, HTTPException, Request
import httpx

from agents import DomainAgent, Agent, CollaborationProtocol
from domains import natural_language_processing, audio_processing, computer_vision

app = FastAPI()


DOMAIN_MODULES: Dict[str, Any] = {
    "nlp": natural_language_processing,
    "audio": audio_processing,
    "vision": computer_vision,
}


class AgentHub:
    """In-memory registry for agents and collaboration protocols."""

    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}
        self._protocols: Dict[str, CollaborationProtocol] = {}

    # -- Agent lifecycle -------------------------------------------------
    def register(self, name: str, domain_key: str) -> None:
        try:
            module = DOMAIN_MODULES[domain_key]
        except KeyError as exc:
            raise HTTPException(
                status_code=404, detail=f"Unknown domain: {domain_key}"
            ) from exc
        agent = DomainAgent(module)
        agent.setup()
        self._agents[name] = agent
        self._last_train.pop(name, None)
        self._last_run.pop(name, None)

    def deregister(self, name: str) -> None:
        agent = self._agents.pop(name, None)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not registered")
        agent.teardown()

    def list_agents(self) -> Iterable[str]:
        return self._agents.keys()

    def train(self, name: str, data: Any) -> Any:
        agent = self._agents.get(name)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not registered")
        plan = agent.train(data)
        self._last_train[name] = plan
        return {"plan": []}

    def run(self, name: str, task: Any) -> Dict[str, Any]:
        agent = self._agents.get(name)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not registered")
        result = agent.execute(task)
        self._last_run[name] = result
        return {"results": []}


hub = AgentHub()

ACTIONS_URL = os.getenv("ACTIONS_URL", "http://localhost:3000/api/actions/execute")
PROXY_URL = os.getenv("PROXY_URL", "http://localhost:11434/v1/chat/completions")
MARKETPLACE_URL = os.getenv("MARKETPLACE_URL", "https://example.com/agents")

@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/pipeline/sample")
async def pipeline_sample():
    async with httpx.AsyncClient() as client:
        try:
            action = await client.post(
                ACTIONS_URL, json={"action": "get_system_info"}
            )
            action.raise_for_status()
            action_data = action.json()
        except httpx.HTTPError as exc:
            return {"error": f"Action service unreachable: {exc}"}

        try:
            proxy = await client.post(
                PROXY_URL, json={"model": "dummy", "messages": []}
            )
            proxy.raise_for_status()
            proxy_data = proxy.json()
        except httpx.HTTPError as exc:
            return {
                "action": action_data,
                "error": f"Proxy service unreachable: {exc}",
            }

    return {"action": action_data, "proxy": proxy_data}


@app.post("/agents/{name}")
async def register_agent(name: str, domain: str):
    """Register a new agent bound to a capability domain."""

    hub.register(name, domain)
    return {"ok": True}


@app.get("/agents")
async def list_agents():
    """Return the names of registered agents."""

    return {"agents": list(hub.list_agents())}


@app.delete("/agents/{name}")
async def remove_agent(name: str):
    """Deregister an agent and release its resources."""

    hub.deregister(name)
    return {"ok": True}


@app.post("/agents/{name}/train")
async def train_agent(name: str, request: Request):
    payload = await request.json()
    data = payload.get("data")
    result = hub.train(name, data)
    return {"result": result}


@app.post("/agents/{name}/run")
async def run_agent(name: str, request: Request):
    payload = await request.json()
    task = payload.get("task")
    result = hub.run(name, task)
    return {"result": result}


@app.get("/marketplace")
async def marketplace():
    """Fetch available agents from a remote marketplace."""

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(MARKETPLACE_URL)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            return {"agents": [], "error": str(exc)}
