from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import yaml

from .backends import LocalBackend, CloudBackend, SearchBackend


@dataclass
class SearchEngine:
    """Wrapper around a pluggable search backend."""

    backend: SearchBackend

    def index(self, docs: Dict[str, str]) -> None:
        self.backend.index(docs)

    def search(self, query: str, top_k: int = 5):
        return self.backend.search(query, top_k=top_k)


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
    return SearchEngine(backend)

__all__ = ["SearchEngine", "load_engine", "LocalBackend", "CloudBackend"]
