"""
Search Service - High-level search orchestration for Windows AI.

Provides a unified :class:`SearchService` that wraps local and remote search
backends, semantic vector search, hybrid scoring, auto-complete suggestions,
and operational statistics behind a single async-first API.

Dependencies
------------
The service works with zero extra packages (uses the built-in
:class:`~.backends.LocalBackend`).  Optional packages unlock additional
features:

* **httpx** – required for :class:`~.backends.RemoteBackend` and
  :class:`~.backends.CloudBackend`.
* **numpy** – enables cosine-similarity ranking in :meth:`semantic_search`.
* **sentence-transformers** – dense embeddings for :meth:`semantic_search`
  and :meth:`hybrid_search`.

All optional imports are guarded with ``try/except`` so the module is always
safe to import regardless of the installed packages.

Example
-------
::

    service = SearchService(backend="local")
    await service.initialize()
    n = await service.index_documents([
        {"id": "doc1", "text": "hello world", "title": "Greeting"},
        {"id": "doc2", "text": "goodbye world", "title": "Farewell"},
    ])
    results = await service.search("hello")
    stats = await service.get_stats()
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set

from .backends import CloudBackend, LocalBackend, RemoteBackend, SearchBackend
from .embeddings import embed as _token_embed
from .index import SearchIndex

logger = logging.getLogger(__name__)

try:
    import numpy as np  # type: ignore
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Return the cosine similarity between two equal-length vectors."""
    if not _NUMPY_AVAILABLE:
        # Pure-Python fallback – adequate for small dimensions
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = sum(x * x for x in a) ** 0.5
        mag_b = sum(x * x for x in b) ** 0.5
        if mag_a == 0.0 or mag_b == 0.0:
            return 0.0
        return dot / (mag_a * mag_b)

    va = np.array(a, dtype=float)
    vb = np.array(b, dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom == 0.0:
        return 0.0
    return float(np.dot(va, vb) / denom)


# ---------------------------------------------------------------------------
# SearchService
# ---------------------------------------------------------------------------

class SearchService:
    """High-level search service for Windows AI.

    Wraps a :class:`~.backends.SearchBackend` and exposes keyword, semantic,
    and hybrid search together with auto-complete suggestions and health /
    statistics endpoints.

    Args:
        backend: Backend selector – ``"local"``, ``"remote"``, or ``"cloud"``.
        config: Optional dictionary with backend-specific settings:

            * ``base_url`` (str) – required for ``"remote"`` / ``"cloud"``
              backends.
            * ``api_key`` (str) – API key / bearer token for remote backends.
            * ``timeout`` (float) – HTTP timeout in seconds (default ``10``).
            * ``st_model`` (str) – ``sentence-transformers`` model name used
              for semantic search (default ``"all-MiniLM-L6-v2"``).
            * ``hybrid_alpha`` (float) – Weight in ``[0, 1]`` blending keyword
              (``0``) vs. semantic (``1``) scores in hybrid search
              (default ``0.5``).

    Example::

        service = SearchService(backend="local")
        await service.initialize()
        await service.index_documents([{"id": "a", "text": "hello world"}])
        results = await service.search("hello")
    """

    def __init__(
        self,
        backend: str = "local",
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._backend_name = backend.lower()
        self._cfg: Dict[str, Any] = config or {}
        self._backend: Optional[SearchBackend] = None
        self._initialized: bool = False

        # Semantic / dense-embedding state
        self._st_model: Optional[Any] = None  # SentenceTransformer instance
        self._dense_index: Dict[str, List[float]] = {}  # doc_id → embedding
        self._doc_store: Dict[str, Dict[str, Any]] = {}  # doc_id → full doc

        # Auto-complete trie (prefix → set of completion strings)
        self._completions: Dict[str, Set[str]] = defaultdict(set)

        # Operational counters
        self._stats: Dict[str, Any] = {
            "total_indexed": 0,
            "total_searches": 0,
            "total_semantic_searches": 0,
            "total_hybrid_searches": 0,
            "total_suggestion_lookups": 0,
            "errors": 0,
            "initialized_at": None,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self) -> bool:
        """Initialize the search service and the underlying backend.

        Should be called once before any other method.

        Returns:
            ``True`` if initialization succeeded, ``False`` otherwise.
        """
        if self._initialized:
            logger.warning("SearchService already initialized")
            return True

        try:
            self._backend = self._build_backend()
            logger.info("SearchService: backend=%s ready", self._backend_name)

            # Attempt to load sentence-transformers model for semantic search
            st_model_name = self._cfg.get("st_model", "all-MiniLM-L6-v2")
            if _ST_AVAILABLE:
                try:
                    self._st_model = await asyncio.to_thread(
                        SentenceTransformer, st_model_name
                    )
                    logger.info("SearchService: semantic model '%s' loaded", st_model_name)
                except Exception as exc:  # model download may fail offline
                    logger.warning(
                        "SearchService: could not load semantic model '%s': %s",
                        st_model_name,
                        exc,
                    )
            else:
                logger.debug(
                    "SearchService: sentence-transformers not installed; "
                    "semantic search will use token-overlap fallback"
                )

            self._initialized = True
            self._stats["initialized_at"] = time.time()
            return True

        except Exception as exc:
            logger.error("SearchService.initialize failed: %s", exc)
            self._stats["errors"] += 1
            return False

    def _build_backend(self) -> SearchBackend:
        """Instantiate the chosen backend from *self._cfg*."""
        name = self._backend_name
        if name == "remote":
            base_url = self._cfg.get("base_url", "http://localhost:9200")
            api_key = self._cfg.get("api_key", "")
            timeout = float(self._cfg.get("timeout", 10.0))
            return RemoteBackend(base_url=base_url, api_key=api_key, timeout=timeout)
        if name == "cloud":
            endpoint = self._cfg.get("base_url", self._cfg.get("endpoint", ""))
            timeout = float(self._cfg.get("timeout", 5.0))
            return CloudBackend(endpoint=endpoint, timeout=timeout)
        # Default: local in-memory backend
        return LocalBackend()

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    async def index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """Index a list of document dictionaries.

        Each document **must** contain an ``"id"`` key and either a ``"text"``
        or ``"content"`` key with the textual body to index.  Any additional
        fields (e.g. ``"title"``, ``"url"``, ``"metadata"``) are stored and
        returned verbatim in search results.

        Args:
            documents: List of document dicts, each with at minimum
                ``{"id": "...", "text": "..."}``.

        Returns:
            Number of documents successfully indexed.

        Raises:
            RuntimeError: If :meth:`initialize` has not been called.
        """
        if not self._initialized or self._backend is None:
            raise RuntimeError("SearchService has not been initialized – call initialize() first")

        if not documents:
            return 0

        indexed = 0
        raw_docs: Dict[str, str] = {}

        for doc in documents:
            doc_id = str(doc.get("id", ""))
            text = str(doc.get("text") or doc.get("content") or "").strip()
            if not doc_id or not text:
                logger.debug("Skipping document with missing id or text: %s", doc)
                continue

            raw_docs[doc_id] = text
            self._doc_store[doc_id] = doc

            # Build completion index from significant words
            for token in text.lower().split():
                if len(token) >= 3:
                    for length in range(3, min(len(token) + 1, 12)):
                        self._completions[token[:length]].add(token)

            # Dense embedding for semantic search
            if self._st_model is not None:
                try:
                    embedding = await asyncio.to_thread(
                        self._st_model.encode, text
                    )
                    self._dense_index[doc_id] = list(map(float, embedding))
                except Exception as exc:
                    logger.warning("Could not compute embedding for doc %s: %s", doc_id, exc)

            indexed += 1

        # Persist to backend (may be remote HTTP call)
        try:
            await asyncio.to_thread(self._backend.index, raw_docs)
        except Exception as exc:
            logger.error("Backend.index failed: %s", exc)
            self._stats["errors"] += 1

        self._stats["total_indexed"] += indexed
        return indexed

    # ------------------------------------------------------------------
    # Search methods
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Keyword-based search.

        Delegates to the underlying backend and enriches the raw document-id
        results with stored document metadata.  Optional *filters* are applied
        as a post-processing step (exact-match on document fields).

        Args:
            query: The search query string.
            filters: Optional dict of ``{field: value}`` pairs.  Only
                documents where every listed field equals the given value are
                returned.
            top_k: Maximum number of results to return.

        Returns:
            List of document dicts ordered by relevance, each containing at
            minimum ``"id"`` and ``"score"`` keys.

        Raises:
            RuntimeError: If :meth:`initialize` has not been called.
        """
        if not self._initialized or self._backend is None:
            raise RuntimeError("SearchService has not been initialized – call initialize() first")

        self._stats["total_searches"] += 1

        if not query:
            return []

        try:
            doc_ids = await asyncio.to_thread(self._backend.search, query, top_k * 2)
        except Exception as exc:
            logger.error("Backend.search failed: %s", exc)
            self._stats["errors"] += 1
            return []

        results: List[Dict[str, Any]] = []
        total = max(len(doc_ids), 1)
        for rank, doc_id in enumerate(doc_ids):
            doc = dict(self._doc_store.get(doc_id, {"id": doc_id}))
            doc["id"] = doc_id
            doc["score"] = round(1.0 - rank / total, 4)
            doc.setdefault("search_type", "keyword")

            if filters and not self._matches_filters(doc, filters):
                continue
            results.append(doc)
            if len(results) >= top_k:
                break

        return results

    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Dense-vector semantic search.

        When ``sentence-transformers`` is installed and a model was loaded
        during :meth:`initialize`, encodes the query and ranks documents by
        cosine similarity.  Falls back to token-overlap keyword search
        automatically when the dense index is empty or the model is
        unavailable.

        Args:
            query: The natural-language query string.
            top_k: Maximum number of results to return.

        Returns:
            List of document dicts ordered by cosine similarity (descending),
            each containing ``"id"``, ``"score"``, and
            ``"search_type": "semantic"`` keys.

        Raises:
            RuntimeError: If :meth:`initialize` has not been called.
        """
        if not self._initialized:
            raise RuntimeError("SearchService has not been initialized – call initialize() first")

        self._stats["total_semantic_searches"] += 1

        if not query:
            return []

        # Dense-vector path
        if self._st_model is not None and self._dense_index:
            try:
                query_vec = await asyncio.to_thread(self._st_model.encode, query)
                query_vec_list = list(map(float, query_vec))

                scored = []
                for doc_id, doc_vec in self._dense_index.items():
                    sim = _cosine_similarity(query_vec_list, doc_vec)
                    scored.append((sim, doc_id))

                scored.sort(reverse=True)
                results = []
                for sim, doc_id in scored[:top_k]:
                    doc = dict(self._doc_store.get(doc_id, {"id": doc_id}))
                    doc["id"] = doc_id
                    doc["score"] = round(sim, 4)
                    doc["search_type"] = "semantic"
                    results.append(doc)
                return results
            except Exception as exc:
                logger.warning("Semantic search failed (%s); falling back to keyword", exc)

        # Token-overlap fallback
        logger.debug("semantic_search: using token-overlap fallback for query=%r", query)
        token_index = SearchIndex(_token_embed)
        for doc_id, doc in self._doc_store.items():
            text = str(doc.get("text") or doc.get("content") or "")
            token_index.add_document(doc_id, text)

        doc_ids = token_index.query(query, top_k=top_k)
        results = []
        total = max(len(doc_ids), 1)
        for rank, doc_id in enumerate(doc_ids):
            doc = dict(self._doc_store.get(doc_id, {"id": doc_id}))
            doc["id"] = doc_id
            doc["score"] = round(1.0 - rank / total, 4)
            doc["search_type"] = "semantic_fallback"
            results.append(doc)
        return results

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Hybrid keyword + semantic search with score fusion.

        Runs both :meth:`search` and :meth:`semantic_search` concurrently and
        fuses their scores using a linear interpolation controlled by the
        ``hybrid_alpha`` config key (default ``0.5``).

        A score of ``0.0`` means pure keyword; ``1.0`` means pure semantic.

        Args:
            query: The search query string.
            top_k: Maximum number of results to return.

        Returns:
            List of document dicts ordered by fused score (descending), each
            containing ``"id"``, ``"score"``, and
            ``"search_type": "hybrid"`` keys.

        Raises:
            RuntimeError: If :meth:`initialize` has not been called.
        """
        if not self._initialized:
            raise RuntimeError("SearchService has not been initialized – call initialize() first")

        self._stats["total_hybrid_searches"] += 1

        if not query:
            return []

        alpha = float(self._cfg.get("hybrid_alpha", 0.5))
        alpha = max(0.0, min(1.0, alpha))

        # Fetch both result sets concurrently
        keyword_results, semantic_results = await asyncio.gather(
            self.search(query, top_k=top_k * 2),
            self.semantic_search(query, top_k=top_k * 2),
            return_exceptions=True,
        )

        if isinstance(keyword_results, Exception):
            logger.warning("hybrid_search keyword leg failed: %s", keyword_results)
            keyword_results = []
        if isinstance(semantic_results, Exception):
            logger.warning("hybrid_search semantic leg failed: %s", semantic_results)
            semantic_results = []

        # Build score maps
        kw_scores: Dict[str, float] = {r["id"]: r["score"] for r in keyword_results}  # type: ignore[union-attr]
        sem_scores: Dict[str, float] = {r["id"]: r["score"] for r in semantic_results}  # type: ignore[union-attr]

        all_ids: Set[str] = set(kw_scores) | set(sem_scores)
        fused: List[tuple[float, str]] = []
        for doc_id in all_ids:
            kw = kw_scores.get(doc_id, 0.0)
            sem = sem_scores.get(doc_id, 0.0)
            score = (1.0 - alpha) * kw + alpha * sem
            fused.append((score, doc_id))

        fused.sort(reverse=True)

        results = []
        for score, doc_id in fused[:top_k]:
            doc = dict(self._doc_store.get(doc_id, {"id": doc_id}))
            doc["id"] = doc_id
            doc["score"] = round(score, 4)
            doc["search_type"] = "hybrid"
            results.append(doc)

        return results

    # ------------------------------------------------------------------
    # Suggestions / auto-complete
    # ------------------------------------------------------------------

    async def get_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        """Return auto-complete suggestions for *prefix*.

        Uses a simple prefix-trie built during indexing.  Suggestions are
        sorted alphabetically (case-insensitive).

        Args:
            prefix: The typed prefix string (lowercased automatically).
            limit: Maximum number of suggestions to return.

        Returns:
            Sorted list of candidate completion strings.
        """
        self._stats["total_suggestion_lookups"] += 1

        key = prefix.lower().strip()
        if not key:
            return []

        candidates = self._completions.get(key, set())
        return sorted(candidates)[:limit]

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    async def get_stats(self) -> Dict[str, Any]:
        """Return operational statistics for the search service.

        Returns:
            Dictionary containing counters for indexed documents, search
            calls, errors, backend name, and initialization timestamp.
        """
        return {
            "backend": self._backend_name,
            "initialized": self._initialized,
            "indexed_document_count": len(self._doc_store),
            "dense_index_size": len(self._dense_index),
            "semantic_model_loaded": self._st_model is not None,
            "completion_prefix_count": len(self._completions),
            **self._stats,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _matches_filters(doc: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Return ``True`` if *doc* satisfies all *filters* (exact match)."""
        for field, value in filters.items():
            if doc.get(field) != value:
                return False
        return True

    # ------------------------------------------------------------------
    # Context-manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "SearchService":
        await self.initialize()
        return self

    async def __aexit__(self, *_: Any) -> None:
        # Nothing to clean up for local backend; subclasses may override
        pass


__all__ = ["SearchService"]
