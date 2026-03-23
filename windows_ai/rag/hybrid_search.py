"""Hybrid Search for RAG Pipeline.

Combines BM25 (sparse) and dense vector search for better retrieval quality.
Uses rank fusion to merge results from both retrieval strategies.
"""

from __future__ import annotations

import math
import re
import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""
    doc_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"  # "bm25", "vector", "hybrid"


# ---------------------------------------------------------------------------
# BM25 Implementation
# ---------------------------------------------------------------------------

class BM25Index:
    """Okapi BM25 text search index.

    A lightweight in-memory BM25 implementation that does not require
    external dependencies.

    Parameters
    ----------
    k1 : float
        Term frequency saturation parameter (default 1.5).
    b : float
        Length normalization parameter (default 0.75).
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self._docs: Dict[str, str] = {}
        self._doc_lengths: Dict[str, int] = {}
        self._avg_doc_length: float = 0.0
        self._term_freqs: Dict[str, Dict[str, int]] = {}  # doc_id -> {term: count}
        self._doc_freqs: Dict[str, int] = defaultdict(int)  # term -> num docs containing it
        self._total_docs: int = 0

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple whitespace + punctuation tokenizer with lowercasing."""
        return re.findall(r"\w+", text.lower())

    def add_document(self, doc_id: str, content: str) -> None:
        """Add a document to the index."""
        tokens = self._tokenize(content)
        self._docs[doc_id] = content
        self._doc_lengths[doc_id] = len(tokens)
        tf = Counter(tokens)
        self._term_freqs[doc_id] = dict(tf)

        for term in set(tokens):
            self._doc_freqs[term] += 1

        self._total_docs = len(self._docs)
        self._avg_doc_length = (
            sum(self._doc_lengths.values()) / self._total_docs
            if self._total_docs
            else 0.0
        )

    def remove_document(self, doc_id: str) -> bool:
        """Remove a document from the index."""
        if doc_id not in self._docs:
            return False
        tf = self._term_freqs.pop(doc_id, {})
        for term in tf:
            self._doc_freqs[term] -= 1
            if self._doc_freqs[term] <= 0:
                del self._doc_freqs[term]
        self._docs.pop(doc_id, None)
        self._doc_lengths.pop(doc_id, None)
        self._total_docs = len(self._docs)
        self._avg_doc_length = (
            sum(self._doc_lengths.values()) / self._total_docs
            if self._total_docs
            else 0.0
        )
        return True

    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search the index with BM25 scoring."""
        tokens = self._tokenize(query)
        if not tokens:
            return []

        scores: Dict[str, float] = defaultdict(float)
        n = self._total_docs

        for term in tokens:
            df = self._doc_freqs.get(term, 0)
            if df == 0:
                continue
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1.0)

            for doc_id, tf_map in self._term_freqs.items():
                tf = tf_map.get(term, 0)
                if tf == 0:
                    continue
                dl = self._doc_lengths[doc_id]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * dl / self._avg_doc_length
                )
                scores[doc_id] += idf * numerator / denominator

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            SearchResult(
                doc_id=doc_id,
                content=self._docs[doc_id],
                score=score,
                source="bm25",
            )
            for doc_id, score in ranked
        ]

    @property
    def document_count(self) -> int:
        return self._total_docs


# ---------------------------------------------------------------------------
# Dense Vector Index (in-memory cosine similarity)
# ---------------------------------------------------------------------------

class VectorIndex:
    """Simple in-memory dense vector search using cosine similarity.

    For production use, swap with FAISS, Qdrant, or Pinecone backends
    from ``windows_ai.vector_db``.
    """

    def __init__(self) -> None:
        self._vectors: Dict[str, List[float]] = {}
        self._docs: Dict[str, str] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def add_document(
        self,
        doc_id: str,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a document with its embedding."""
        self._vectors[doc_id] = embedding
        self._docs[doc_id] = content
        self._metadata[doc_id] = metadata or {}

    def remove_document(self, doc_id: str) -> bool:
        if doc_id not in self._vectors:
            return False
        self._vectors.pop(doc_id, None)
        self._docs.pop(doc_id, None)
        self._metadata.pop(doc_id, None)
        return True

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query_embedding: List[float], top_k: int = 10) -> List[SearchResult]:
        """Find the most similar documents to *query_embedding*."""
        scores: List[Tuple[str, float]] = []
        for doc_id, vec in self._vectors.items():
            sim = self._cosine_similarity(query_embedding, vec)
            scores.append((doc_id, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [
            SearchResult(
                doc_id=doc_id,
                content=self._docs[doc_id],
                score=score,
                metadata=self._metadata.get(doc_id, {}),
                source="vector",
            )
            for doc_id, score in scores[:top_k]
        ]

    @property
    def document_count(self) -> int:
        return len(self._vectors)


# ---------------------------------------------------------------------------
# Hybrid Search (Reciprocal Rank Fusion)
# ---------------------------------------------------------------------------

class HybridSearch:
    """Combine BM25 and vector search results using Reciprocal Rank Fusion.

    Parameters
    ----------
    bm25_weight : float
        Weight for BM25 results in fusion (default 0.5).
    vector_weight : float
        Weight for vector results in fusion (default 0.5).
    rrf_k : int
        RRF constant (default 60, per the original paper).
    """

    def __init__(
        self,
        bm25_weight: float = 0.5,
        vector_weight: float = 0.5,
        rrf_k: int = 60,
    ) -> None:
        self.bm25 = BM25Index()
        self.vector = VectorIndex()
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.rrf_k = rrf_k

    def add_document(
        self,
        doc_id: str,
        content: str,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add a document to both BM25 and (optionally) vector indices."""
        self.bm25.add_document(doc_id, content)
        if embedding is not None:
            self.vector.add_document(doc_id, content, embedding, metadata)

    def remove_document(self, doc_id: str) -> None:
        self.bm25.remove_document(doc_id)
        self.vector.remove_document(doc_id)

    def search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        top_k: int = 10,
    ) -> List[SearchResult]:
        """Perform hybrid search with rank fusion.

        If *query_embedding* is not provided, falls back to BM25-only.
        """
        bm25_results = self.bm25.search(query, top_k=top_k * 2)

        if query_embedding is not None and self.vector.document_count > 0:
            vector_results = self.vector.search(query_embedding, top_k=top_k * 2)
            return self._fuse(bm25_results, vector_results, top_k)

        # BM25-only fallback
        for r in bm25_results[:top_k]:
            r.source = "hybrid"
        return bm25_results[:top_k]

    def _fuse(
        self,
        bm25_results: List[SearchResult],
        vector_results: List[SearchResult],
        top_k: int,
    ) -> List[SearchResult]:
        """Reciprocal Rank Fusion of two result lists."""
        scores: Dict[str, float] = defaultdict(float)
        result_map: Dict[str, SearchResult] = {}

        for rank, r in enumerate(bm25_results):
            rrf_score = self.bm25_weight / (self.rrf_k + rank + 1)
            scores[r.doc_id] += rrf_score
            result_map[r.doc_id] = r

        for rank, r in enumerate(vector_results):
            rrf_score = self.vector_weight / (self.rrf_k + rank + 1)
            scores[r.doc_id] += rrf_score
            if r.doc_id not in result_map:
                result_map[r.doc_id] = r

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [
            SearchResult(
                doc_id=doc_id,
                content=result_map[doc_id].content,
                score=score,
                metadata=result_map[doc_id].metadata,
                source="hybrid",
            )
            for doc_id, score in ranked
        ]

    def stats(self) -> Dict[str, Any]:
        return {
            "bm25_documents": self.bm25.document_count,
            "vector_documents": self.vector.document_count,
            "bm25_weight": self.bm25_weight,
            "vector_weight": self.vector_weight,
        }
