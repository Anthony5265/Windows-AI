from typing import Dict, Any, Optional, List

try:  # Optional dependency
    import requests  # type: ignore
except Exception:  # pragma: no cover - graceful fallback
    requests = None  # type: ignore

class WindowsAIClient:
    """Simple client for the Windows AI Actions API."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip('/')

    def _post(self, path: str, payload: Dict[str, Any]) -> Any:
        if requests is None:
            raise RuntimeError("The 'requests' package is required to use WindowsAIClient")
        res = requests.post(f"{self.base_url}{path}", json=payload)
        res.raise_for_status()
        return res

    def execute_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        res = self._post("/api/actions/execute", {"action": action, "params": params or {}})
        return res.json()["result"]

    def mobile_pair(self, device_id: str) -> str:
        res = self._post("/api/mobile/pair", {"deviceId": device_id})
        return res.json()["token"]

    def mobile_command(self, token: str, action: str, params: Optional[Dict[str, Any]] = None) -> Any:
        res = self._post(
            "/api/mobile/command",
            {"token": token, "action": action, "params": params or {}}
        )
        return res.json()["result"]

    def mesh_distribute(self, task: str) -> Dict[str, Any]:
        res = self._post("/api/mesh/distribute", {"task": task})
        return res.json()["result"]

    def iot_event(self, device_id: str, event: str) -> Dict[str, Any]:
        res = self._post("/api/iot/event", {"deviceId": device_id, "event": event})
        return res.json()["result"]

    def search_query(self, query: str, documents: Optional[Dict[str, str]] = None) -> List[str]:
        res = self._post(
            "/api/search/query",
            {"query": query, "documents": documents or {}}
        )
        return res.json()["result"]
