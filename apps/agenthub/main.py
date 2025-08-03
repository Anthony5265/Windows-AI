from fastapi import FastAPI
import httpx

app = FastAPI()

ACTIONS_URL = "http://localhost:3000/api/actions/execute"
PROXY_URL = "http://localhost:11434/v1/chat/completions"

@app.get("/health")
async def health():
    return {"ok": True}

@app.post("/pipeline/sample")
async def pipeline_sample():
    async with httpx.AsyncClient() as client:
        action = await client.post(ACTIONS_URL, json={"action": "get_system_info"})
        proxy = await client.post(PROXY_URL, json={"model": "dummy", "messages": []})
    return {"action": action.json(), "proxy": proxy.json()}
