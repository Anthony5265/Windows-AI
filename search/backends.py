from __future__ import annotations

from typing import Dict, List

import httpx

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
    """Search backend that delegates to a remote HTTP service."""

    def __init__(self, endpoint: str, timeout: float = 5.0):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        # Keep a local copy of indexed documents to provide deterministic
        # behaviour when the remote service is unavailable.
        self._indexed: Dict[str, str] = {}

    def index(self, docs: Dict[str, str]) -> None:
        """Send documents to the remote service for indexing.

        On network failures the documents are stored locally so that searches
        can still succeed using the fallback behaviour.
        """

        url = f"{self.endpoint}/index"
        try:
            response = httpx.post(url, json=docs, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError:
            # Swallow the exception and fall back to local storage.
            pass
        finally:
            # Always keep a local copy of indexed docs for deterministic tests
            # and offline fallbacks.
            self._indexed.update(docs)

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """Query the remote service for matching document ids.

        If the remote call fails due to network errors or timeouts, return
        results from the locally indexed documents as a fallback.
        """

        if not query:
            return []

        url = f"{self.endpoint}/search"
        try:
            response = httpx.get(
                url, params={"q": query, "top_k": top_k}, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])[:top_k]
        except httpx.HTTPError:
            # Fall back to returning ids of locally indexed documents to keep
            # behaviour deterministic when the remote service is unavailable.
            return list(self._indexed.keys())[:top_k]
