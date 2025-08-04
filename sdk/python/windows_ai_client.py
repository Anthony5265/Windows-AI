import requests
from typing import Dict, Any, Optional, List

class WindowsAIClient:
    """Simple client for the Windows AI Actions API."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip('/')

    def execute_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        res = requests.post(f"{self.base_url}/api/actions/execute", json={"action": action, "params": params or {}})
        res.raise_for_status()
        return res.json()["result"]

    def mobile_pair(self, device_id: str) -> str:
        res = requests.post(f"{self.base_url}/api/mobile/pair", json={"deviceId": device_id})
        res.raise_for_status()
        return res.json()["token"]

    def mobile_command(self, token: str, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        res = requests.post(
            f"{self.base_url}/api/mobile/command",
            json={"token": token, "action": action, "params": params or {}}
        )
        res.raise_for_status()
        return res.json()["result"]

    def mesh_distribute(self, task: str) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/api/mesh/distribute", json={"task": task})
        res.raise_for_status()
        return res.json()["result"]

    def iot_event(self, device_id: str, event: str) -> Dict[str, Any]:
        res = requests.post(f"{self.base_url}/api/iot/event", json={"deviceId": device_id, "event": event})
        res.raise_for_status()
        return res.json()["result"]

    def search_query(self, query: str, documents: Optional[Dict[str, str]] = None) -> List[str]:
        res = requests.post(
            f"{self.base_url}/api/search/query",
            json={"query": query, "documents": documents or {}}
        )
        res.raise_for_status()
        return res.json()["result"]
