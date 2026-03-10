from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional

try:
    import httpx
    _HTTPX_AVAILABLE = True
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]
    _HTTPX_AVAILABLE = False

from .embeddings import embed
from .index import SearchIndex

logger = logging.getLogger(__name__)


class SearchBackend:
    """Abstract search backend interface.

    Subclasses must implement :meth:`index` and :meth:`search`.
    """

    def index(self, docs: Dict[str, str]) -> None:  # pragma: no cover - interface
        """Index a mapping of document-id → text.

        Args:
            docs: Dictionary mapping document identifiers to their text content.

        Raises:
            NotImplementedError: Must be overridden by subclasses.
        """
        raise NotImplementedError

    def search(self, query: str, top_k: int = 5) -> List[str]:  # pragma: no cover - interface
        """Return the top-k document ids most relevant to *query*.

        Args:
            query: The search query string.
            top_k: Maximum number of results to return.

        Returns:
            Ordered list of document identifiers.

        Raises:
            NotImplementedError: Must be overridden by subclasses.
        """
        raise NotImplementedError


class LocalBackend(SearchBackend):
    """Simple in-memory search backend backed by :class:`~.index.SearchIndex`.

    Uses token-overlap scoring via :func:`~.embeddings.embed`.  Suitable for
    small corpora and unit tests; no external dependencies required.

    Example::

        backend = LocalBackend()
        backend.index({"doc1": "hello world", "doc2": "goodbye world"})
        results = backend.search("hello", top_k=1)
        assert results == ["doc1"]
    """

    def __init__(self) -> None:
        self._index: SearchIndex = SearchIndex(embed)

    def index(self, docs: Dict[str, str]) -> None:
        """Add or update *docs* in the in-memory index.

        Args:
            docs: Dictionary mapping document identifiers to text content.
        """
        for doc_id, text in docs.items():
            self._index.add_document(doc_id, text)

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """Return document ids ranked by token overlap with *query*.

        Args:
            query: The search query string.
            top_k: Maximum number of results to return.

        Returns:
            Ordered list of document identifiers (best match first).
        """
        return self._index.query(query, top_k=top_k)


class CloudBackend(SearchBackend):
    """Search backend that delegates to a remote HTTP service.

    Falls back to returning locally-tracked document ids when the remote
    service is unavailable, keeping behaviour deterministic in tests.

    Args:
        endpoint: Base URL of the remote search service.
        timeout: HTTP request timeout in seconds.
    """

    def __init__(self, endpoint: str, timeout: float = 5.0) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        self._indexed: Dict[str, str] = {}

    def index(self, docs: Dict[str, str]) -> None:
        """Send *docs* to the remote service for indexing.

        Always stores docs locally as a fallback for when the remote is
        unreachable.

        Args:
            docs: Dictionary mapping document identifiers to text content.
        """
        if not _HTTPX_AVAILABLE:
            logger.warning("httpx not installed; CloudBackend storing docs locally only")
            self._indexed.update(docs)
            return

        url = f"{self.endpoint}/index"
        try:
            response = httpx.post(url, json=docs, timeout=self.timeout)
            response.raise_for_status()
        except (httpx.RequestError, httpx.HTTPStatusError, httpx.TimeoutException) as exc:
            logger.warning("CloudBackend.index remote call failed (%s); stored locally", exc)
        finally:
            self._indexed.update(docs)

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """Query the remote service; fall back to local doc ids on failure.

        Args:
            query: The search query string.
            top_k: Maximum number of results to return.

        Returns:
            Ordered list of document identifiers.
        """
        if not query:
            return []

        if not _HTTPX_AVAILABLE:
            logger.warning("httpx not installed; CloudBackend returning local ids")
            return list(self._indexed.keys())[:top_k]

        url = f"{self.endpoint}/search"
        try:
            response = httpx.get(
                url, params={"q": query, "top_k": top_k}, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])[:top_k]
        except (
            httpx.RequestError,
            httpx.HTTPStatusError,
            httpx.TimeoutException,
            ValueError,
        ) as exc:
            logger.warning("CloudBackend.search remote call failed (%s); using local fallback", exc)
            return list(self._indexed.keys())[:top_k]


class RemoteBackend(SearchBackend):
    """HTTP-based search backend compatible with Elasticsearch, Typesense, etc.

    Supports both synchronous and asynchronous index / search operations.
    When *httpx* is unavailable the backend degrades gracefully by storing
    documents in-memory and performing token-overlap search via the
    :class:`LocalBackend`.

    Args:
        base_url: Root URL of the search service (e.g. ``http://localhost:9200``).
        api_key: Optional bearer token or API key sent as an
            ``Authorization`` header.
        index_path: URL path appended to *base_url* for indexing requests.
        search_path: URL path appended to *base_url* for search requests.
        timeout: HTTP request timeout in seconds.
        headers: Additional HTTP headers to include in every request.

    Example::

        backend = RemoteBackend(
            base_url="http://localhost:9200",
            api_key="my-secret-key",
        )
        backend.index({"doc1": "hello world"})
        results = backend.search("hello", top_k=5)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        index_path: str = "/index",
        search_path: str = "/search",
        timeout: float = 10.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.index_path = index_path
        self.search_path = search_path
        self.timeout = timeout
        self._extra_headers: Dict[str, str] = headers or {}

        # Local fallback used when remote is unreachable
        self._fallback = LocalBackend()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> Dict[str, str]:
        """Build the HTTP headers for each request."""
        hdrs: Dict[str, str] = {"Content-Type": "application/json"}
        hdrs.update(self._extra_headers)
        if self.api_key:
            hdrs["Authorization"] = f"Bearer {self.api_key}"
        return hdrs

    # ------------------------------------------------------------------
    # Synchronous interface
    # ------------------------------------------------------------------

    def index(self, docs: Dict[str, str]) -> None:
        """Index *docs* via a synchronous HTTP POST to the remote service.

        Falls back to the in-memory :class:`LocalBackend` on any network or
        HTTP error so that subsequent :meth:`search` calls still succeed.

        Args:
            docs: Dictionary mapping document identifiers to text content.
        """
        # Always keep local fallback up-to-date
        self._fallback.index(docs)

        if not _HTTPX_AVAILABLE:
            logger.debug("RemoteBackend: httpx unavailable, using local-only indexing")
            return

        url = f"{self.base_url}{self.index_path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=docs, headers=self._build_headers())
                response.raise_for_status()
            logger.debug("RemoteBackend.index: indexed %d docs to %s", len(docs), url)
        except Exception as exc:  # broad – any HTTP / network failure
            logger.warning("RemoteBackend.index failed (%s); local fallback active", exc)

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """Search the remote service; fall back to local index on failure.

        Args:
            query: The search query string.
            top_k: Maximum number of results to return.

        Returns:
            Ordered list of document identifiers (best match first).
        """
        if not query:
            return []

        if not _HTTPX_AVAILABLE:
            logger.debug("RemoteBackend: httpx unavailable, using local search fallback")
            return self._fallback.search(query, top_k=top_k)

        url = f"{self.base_url}{self.search_path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(
                    url,
                    params={"q": query, "top_k": top_k},
                    headers=self._build_headers(),
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])[:top_k]
        except Exception as exc:
            logger.warning("RemoteBackend.search failed (%s); using local fallback", exc)
            return self._fallback.search(query, top_k=top_k)

    # ------------------------------------------------------------------
    # Asynchronous interface
    # ------------------------------------------------------------------

    async def index_async(self, docs: Dict[str, str]) -> None:
        """Asynchronously index *docs* via an HTTP POST.

        Uses :func:`asyncio.to_thread` to avoid blocking the event loop when
        *httpx* is installed but no async client is available, and falls back
        to :meth:`index` in older Python environments.

        Args:
            docs: Dictionary mapping document identifiers to text content.
        """
        try:
            await asyncio.to_thread(self.index, docs)
        except AttributeError:
            # Python < 3.9 – run in executor instead
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.index, docs)

    async def search_async(self, query: str, top_k: int = 5) -> List[str]:
        """Asynchronously search the remote service.

        Args:
            query: The search query string.
            top_k: Maximum number of results to return.

        Returns:
            Ordered list of document identifiers (best match first).
        """
        if not _HTTPX_AVAILABLE:
            return self._fallback.search(query, top_k=top_k)

        url = f"{self.base_url}{self.search_path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    params={"q": query, "top_k": top_k},
                    headers=self._build_headers(),
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])[:top_k]
        except Exception as exc:
            logger.warning("RemoteBackend.search_async failed (%s); using local fallback", exc)
            return self._fallback.search(query, top_k=top_k)
