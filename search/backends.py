from __future__ import annotations

from typing import Dict, List

import requests

from .embeddings import embed
from .index import SearchIndex


class SearchBackend:
    """Abstract search backend interface."""

    def index(self, docs: Dict[str, str]) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    def search(self, query: str, top_k: int = 5) -> List[str]:  # pragma: no cover - interface
        raise NotImplementedError


class LocalBackend(SearchBackend):
    """Simple in-memory search backend."""

    def __init__(self):
        self._index = SearchIndex(embed)

    def index(self, docs: Dict[str, str]) -> None:
        for doc_id, text in docs.items():
            self._index.add_document(doc_id, text)

    def search(self, query: str, top_k: int = 5) -> List[str]:
        return self._index.query(query, top_k=top_k)


class CloudBackend(SearchBackend):
    """Backend representing a remote search service."""

    def __init__(self, endpoint: str, timeout: float = 5.0):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def index(self, docs: Dict[str, str]) -> None:
        try:
            res = requests.post(
                f"{self.endpoint}/index", json=docs, timeout=self.timeout
            )
            res.raise_for_status()
        except requests.exceptions.Timeout as e:  # pragma: no cover - network
            raise TimeoutError("Index request timed out") from e
        except requests.RequestException as e:  # pragma: no cover - network
            raise RuntimeError(f"Index request failed: {e}") from e

    def search(self, query: str, top_k: int = 5) -> List[str]:
        try:
            res = requests.post(
                f"{self.endpoint}/search",
                json={"query": query, "top_k": top_k},
                timeout=self.timeout,
            )
            res.raise_for_status()
            data = res.json()
            return data.get("results", [])
        except requests.exceptions.Timeout as e:  # pragma: no cover - network
            raise TimeoutError("Search request timed out") from e
        except requests.RequestException as e:  # pragma: no cover - network
            raise RuntimeError(f"Search request failed: {e}") from e
