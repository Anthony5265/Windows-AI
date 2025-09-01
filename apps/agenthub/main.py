import os
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request
import httpx

from windows_ai.agents import DomainAgent, Agent
from domains import natural_language_processing, audio_processing, computer_vision

app = FastAPI()


DOMAIN_MODULES: Dict[str, Any] = {
    "nlp": natural_language_processing,
    "audio": audio_processing,
    "vision": computer_vision,
}


class AgentHub:
    """In-memory registry for agents."""

    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}

    def register(self, name: str, domain_key: str) -> None:
        try:
            module = DOMAIN_MODULES[domain_key]
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown domain: {domain_key}") from exc
        agent = DomainAgent(module)
        agent.setup()
        self._agents[name] = agent

    def train(self, name: str, data: Any) -> Any:
        agent = self._agents.get(name)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not registered")
        return agent.train(data)

    def run(self, name: str, task: Any) -> Any:
        agent = self._agents.get(name)
        if agent is None:
            raise HTTPException(status_code=404, detail="Agent not registered")
        return agent.execute(task)


hub = AgentHub()

ACTIONS_URL = os.getenv("ACTIONS_URL", "http://localhost:3000/api/actions/execute")
PROXY_URL = os.getenv("PROXY_URL", "http://localhost:11434/v1/chat/completions")

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
            return {"action": action_data, "error": f"Proxy service unreachable: {exc}"}

    return {"action": action_data, "proxy": proxy_data}


@app.post("/agents/{name}")
async def register_agent(name: str, domain: str):
    """Register a new agent bound to a capability domain."""

    hub.register(name, domain)
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
