from __future__ import annotations

from typing import Dict, List

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
    """Placeholder backend representing a remote service."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self._indexed: Dict[str, str] = {}

    def index(self, docs: Dict[str, str]) -> None:
        # In a real implementation this would send docs to the service.
        self._indexed.update(docs)

    def search(self, query: str, top_k: int = 5) -> List[str]:
        # Real implementation would call the remote service. We return all ids
        # when a query is provided to keep behaviour deterministic for tests.
        if not query:
            return []
        return list(self._indexed.keys())[:top_k]
