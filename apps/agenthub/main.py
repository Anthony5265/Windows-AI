import os
from fastapi import FastAPI
import httpx

app = FastAPI()

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
