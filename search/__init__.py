from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import httpx
import yaml

from .backends import LocalBackend, CloudBackend, SearchBackend


@dataclass
class SearchEngine:
    """Search engine combining a local backend with remote APIs."""

    backend: SearchBackend
    remote_apis: Optional[Dict[str, str]] = None

    def index(self, docs: Dict[str, str]) -> None:
        """Index *docs* using the underlying backend."""

        self.backend.index(docs)

    # ------------------------------------------------------------------ utils
    def _remote_query(self, endpoint: str, query: str, top_k: int) -> List[str]:
        """Query a remote HTTP endpoint for additional results."""

        try:
            response = httpx.get(
                endpoint, params={"q": query, "top_k": top_k}, timeout=5.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])[:top_k]
        except httpx.HTTPError:
            return []

    # ----------------------------------------------------------------- search
    def search(self, query: str, top_k: int = 5) -> List[str]:
        """Return combined results from the local index and remote APIs."""

        results = self.backend.search(query, top_k=top_k)
        for endpoint in (self.remote_apis or {}).values():
            results.extend(self._remote_query(endpoint, query, top_k))

        # Remove duplicates while preserving order
        seen = set()
        unique: List[str] = []
        for item in results:
            if item not in seen:
                unique.append(item)
                seen.add(item)
        return unique


def load_engine(config_path: str = "config/search.yaml") -> SearchEngine:
    """Create a search engine from the provided configuration file."""

    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f) or {}

    backend_name = cfg.get("backend", "local")
    if backend_name == "cloud":
        endpoint = cfg.get("cloud", {}).get("endpoint", "")
        backend = CloudBackend(endpoint)
    else:
        backend = LocalBackend()

    remotes = cfg.get("remotes", {})
    return SearchEngine(backend, remote_apis=remotes)

__all__ = ["SearchEngine", "load_engine", "LocalBackend", "CloudBackend"]
