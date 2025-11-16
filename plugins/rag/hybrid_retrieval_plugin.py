"""
Hybrid Retrieval Plugin
Combines dense and sparse retrieval methods
"""

from typing import Dict, Any, Optional, List
import numpy as np


class HybridRetrievalPlugin:
    """Plugin for hybrid dense + sparse retrieval"""

    name = "hybrid_retrieval"
    version = "1.0.0"
    description = "Combine dense vector search with sparse keyword retrieval"
    author = "Windows AI Team"

    def __init__(self):
        self.alpha = 0.5  # Weight for dense vs sparse
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Hybrid Retrieval plugin"""
        try:
            self.alpha = config.get("alpha", 0.5) if config else 0.5
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Hybrid Retrieval plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Hybrid Retrieval action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "hybrid_search":
                return self._hybrid_search(params)
            elif action == "bm25_search":
                return self._bm25_search(params)
            elif action == "dense_search":
                return self._dense_search(params)
            elif action == "combine_results":
                return self._combine_results(params)
            elif action == "reciprocal_rank_fusion":
                return self._reciprocal_rank_fusion(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _hybrid_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform hybrid search combining dense and sparse retrieval"""
        query = params.get("query", "")
        documents = params.get("documents", [])
        top_k = params.get("top_k", 10)
        alpha = params.get("alpha", self.alpha)  # 0 = sparse only, 1 = dense only

        # Perform dense search (vector similarity)
        dense_results = self._dense_search({
            "query": query,
            "documents": documents,
            "top_k": len(documents)
        })

        # Perform sparse search (BM25 keyword matching)
        sparse_results = self._bm25_search({
            "query": query,
            "documents": documents,
            "top_k": len(documents)
        })

        # Combine scores
        combined_scores = {}
        for i, doc in enumerate(documents):
            # Get scores from both methods
            dense_score = next((r["score"] for r in dense_results["results"] if r["document"] == doc), 0)
            sparse_score = next((r["score"] for r in sparse_results["results"] if r["document"] == doc), 0)

            # Weighted combination
            combined_score = alpha * dense_score + (1 - alpha) * sparse_score
            combined_scores[i] = {
                "document": doc,
                "score": combined_score,
                "dense_score": dense_score,
                "sparse_score": sparse_score,
                "rank": i
            }

        # Sort by combined score
        results = sorted(combined_scores.values(), key=lambda x: x["score"], reverse=True)[:top_k]

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "alpha": alpha,
            "method": "hybrid"
        }

    def _bm25_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform BM25 sparse keyword search"""
        query = params.get("query", "")
        documents = params.get("documents", [])
        top_k = params.get("top_k", 10)
        k1 = params.get("k1", 1.5)  # Term frequency saturation
        b = params.get("b", 0.75)   # Length normalization

        # Simulated BM25 scoring
        # In production, would use actual BM25 implementation
        query_terms = set(query.lower().split())
        avg_doc_length = sum(len(doc.split()) for doc in documents) / len(documents) if documents else 0

        results = []
        for i, doc in enumerate(documents):
            doc_terms = doc.lower().split()
            doc_length = len(doc_terms)

            # BM25 score calculation (simplified)
            score = 0
            for term in query_terms:
                tf = doc_terms.count(term)
                if tf > 0:
                    # Simplified BM25 formula
                    norm_tf = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_length / avg_doc_length)))
                    idf = np.log(len(documents) / (1 + sum(1 for d in documents if term in d.lower())))
                    score += norm_tf * idf

            results.append({
                "document": doc,
                "score": float(score),
                "rank": i
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:top_k]

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "method": "bm25",
            "parameters": {"k1": k1, "b": b}
        }

    def _dense_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform dense vector similarity search"""
        query = params.get("query", "")
        documents = params.get("documents", [])
        top_k = params.get("top_k", 10)

        # Simulated dense vector search
        # In production, would use actual embeddings and cosine similarity
        results = []
        for i, doc in enumerate(documents):
            # Simulate semantic similarity
            # Higher score for docs with similar concepts
            score = 0.5 + np.random.uniform(-0.3, 0.4)
            # Boost if query terms present
            query_terms = set(query.lower().split())
            doc_terms = set(doc.lower().split())
            overlap = len(query_terms & doc_terms) / len(query_terms) if query_terms else 0
            score += 0.2 * overlap

            results.append({
                "document": doc,
                "score": float(min(score, 1.0)),
                "rank": i
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:top_k]

        return {
            "success": True,
            "query": query,
            "results": results,
            "count": len(results),
            "method": "dense"
        }

    def _combine_results(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Combine results from multiple retrievers using weighted scores"""
        retrievals = params.get("retrievals", [])  # List of retrieval results
        weights = params.get("weights", [])  # Weights for each retrieval method
        top_k = params.get("top_k", 10)

        if not retrievals:
            return {"success": False, "error": "No retrieval results provided"}

        # Default equal weights
        if not weights:
            weights = [1.0 / len(retrievals)] * len(retrievals)

        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        # Combine scores
        combined = {}
        for retrieval, weight in zip(retrievals, weights):
            for result in retrieval.get("results", []):
                doc = result["document"]
                score = result.get("score", 0)

                if doc not in combined:
                    combined[doc] = {"document": doc, "score": 0, "sources": []}

                combined[doc]["score"] += weight * score
                combined[doc]["sources"].append({
                    "method": retrieval.get("method", "unknown"),
                    "score": score,
                    "weight": weight
                })

        # Sort by combined score
        results = sorted(combined.values(), key=lambda x: x["score"], reverse=True)[:top_k]

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "num_sources": len(retrievals),
            "method": "weighted_combination"
        }

    def _reciprocal_rank_fusion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reciprocal Rank Fusion (RRF) for combining rankings

        RRF is a simple but effective method that doesn't require
        normalized scores, just rankings.
        """
        retrievals = params.get("retrievals", [])  # List of retrieval results
        top_k = params.get("top_k", 10)
        k = params.get("k", 60)  # RRF constant

        if not retrievals:
            return {"success": False, "error": "No retrieval results provided"}

        # Calculate RRF scores
        rrf_scores = {}
        for retrieval in retrievals:
            for rank, result in enumerate(retrieval.get("results", [])):
                doc = result["document"]

                if doc not in rrf_scores:
                    rrf_scores[doc] = {
                        "document": doc,
                        "rrf_score": 0,
                        "rankings": []
                    }

                # RRF formula: 1 / (k + rank)
                score = 1.0 / (k + rank + 1)
                rrf_scores[doc]["rrf_score"] += score
                rrf_scores[doc]["rankings"].append({
                    "method": retrieval.get("method", "unknown"),
                    "rank": rank,
                    "contribution": score
                })

        # Sort by RRF score
        results = sorted(rrf_scores.values(), key=lambda x: x["rrf_score"], reverse=True)[:top_k]

        return {
            "success": True,
            "results": results,
            "count": len(results),
            "num_sources": len(retrievals),
            "k": k,
            "method": "reciprocal_rank_fusion"
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
