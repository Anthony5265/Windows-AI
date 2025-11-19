from __future__ import annotations

from typing import Dict, List, Set, Callable


class SearchIndex:
    """In-memory search index using simple token embeddings."""

    def __init__(self, embed_fn: Callable[[str], Set[str]]):
        self._embed = embed_fn
        self._docs: Dict[str, Set[str]] = {}

    def add_document(self, doc_id: str, text: str) -> None:
        """Add or update a document in the index."""

        self._docs[doc_id] = self._embed(text)

    def query(self, text: str, top_k: int = 5) -> List[str]:
        """Return document ids ranked by token overlap."""

        q_vec = self._embed(text)
        scores = []
        for doc_id, vec in self._docs.items():
            score = len(q_vec & vec)
            if score > 0:
                scores.append((score, doc_id))
        scores.sort(reverse=True)
        return [doc_id for score, doc_id in scores[:top_k]]
