"""
Context Compression Plugin
Compress and optimize retrieved context for LLM consumption
"""

from typing import Dict, Any, Optional, List


class ContextCompressionPlugin:
    """Plugin for compressing and optimizing retrieved context"""

    name = "context_compression"
    version = "1.0.0"
    description = "Compress retrieved documents to fit context windows efficiently"
    author = "Windows AI Team"

    def __init__(self):
        self.max_tokens = 2000
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Context Compression plugin"""
        try:
            self.max_tokens = config.get("max_tokens", 2000) if config else 2000
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Context Compression plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Context Compression action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "compress":
                return self._compress(params)
            elif action == "extract_relevant":
                return self._extract_relevant(params)
            elif action == "summarize_context":
                return self._summarize_context(params)
            elif action == "filter_redundant":
                return self._filter_redundant(params)
            elif action == "sliding_window":
                return self._sliding_window(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _compress(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compress documents using multiple strategies"""
        query = params.get("query", "")
        documents = params.get("documents", [])
        max_tokens = params.get("max_tokens", self.max_tokens)
        strategy = params.get("strategy", "extract_relevant")

        if strategy == "extract_relevant":
            result = self._extract_relevant({
                "query": query,
                "documents": documents,
                "max_tokens": max_tokens
            })
        elif strategy == "summarize":
            result = self._summarize_context({
                "documents": documents,
                "max_tokens": max_tokens
            })
        elif strategy == "filter":
            result = self._filter_redundant({
                "documents": documents,
                "max_tokens": max_tokens
            })
        else:
            return {"success": False, "error": f"Unknown strategy: {strategy}"}

        return result

    def _extract_relevant(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extract only query-relevant sentences from documents"""
        query = params.get("query", "")
        documents = params.get("documents", [])
        max_tokens = params.get("max_tokens", self.max_tokens)

        # Simulated relevance extraction
        # In production, would use NLI model or LLM to filter sentences
        query_terms = set(query.lower().split())

        compressed_docs = []
        total_tokens = 0

        for doc in documents:
            sentences = doc.split('. ')
            relevant_sentences = []

            for sentence in sentences:
                sentence_terms = set(sentence.lower().split())
                overlap = len(query_terms & sentence_terms)

                # Keep sentences with query term overlap
                if overlap > 0:
                    relevant_sentences.append(sentence)
                    # Rough token estimate (words * 1.3)
                    tokens = int(len(sentence.split()) * 1.3)
                    total_tokens += tokens

                    if total_tokens >= max_tokens:
                        break

            if relevant_sentences:
                compressed_docs.append('. '.join(relevant_sentences))

            if total_tokens >= max_tokens:
                break

        return {
            "success": True,
            "compressed_documents": compressed_docs,
            "count": len(compressed_docs),
            "estimated_tokens": total_tokens,
            "compression_ratio": total_tokens / (sum(len(d.split()) for d in documents) * 1.3) if documents else 0,
            "method": "extract_relevant"
        }

    def _summarize_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize documents to reduce token count"""
        documents = params.get("documents", [])
        max_tokens = params.get("max_tokens", self.max_tokens)
        summary_ratio = params.get("summary_ratio", 0.3)  # Target 30% of original

        # Simulated summarization
        # In production, would use extractive or abstractive summarization
        summaries = []
        total_tokens = 0

        for doc in documents:
            words = doc.split()
            target_words = int(len(words) * summary_ratio)

            # Simple extractive summary: take first sentences up to target
            summary_words = words[:target_words]
            summary = ' '.join(summary_words)

            tokens = int(len(summary_words) * 1.3)
            total_tokens += tokens

            summaries.append({
                "original_length": len(words),
                "summary_length": len(summary_words),
                "summary": summary,
                "estimated_tokens": tokens
            })

            if total_tokens >= max_tokens:
                break

        return {
            "success": True,
            "summaries": summaries,
            "count": len(summaries),
            "total_estimated_tokens": total_tokens,
            "summary_ratio": summary_ratio,
            "method": "summarize"
        }

    def _filter_redundant(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter redundant or duplicate information"""
        documents = params.get("documents", [])
        max_tokens = params.get("max_tokens", self.max_tokens)
        similarity_threshold = params.get("similarity_threshold", 0.7)

        # Simulated redundancy filtering
        # In production, would use embeddings to detect semantic similarity
        filtered = []
        seen_content = set()
        total_tokens = 0

        for doc in documents:
            # Simple word-based similarity check
            words = set(doc.lower().split())

            # Check if too similar to already selected docs
            is_redundant = False
            for seen_words in seen_content:
                overlap = len(words & seen_words) / len(words | seen_words) if words | seen_words else 0
                if overlap > similarity_threshold:
                    is_redundant = True
                    break

            if not is_redundant:
                tokens = int(len(doc.split()) * 1.3)
                total_tokens += tokens

                if total_tokens <= max_tokens:
                    filtered.append(doc)
                    seen_content.add(frozenset(words))
                else:
                    break

        return {
            "success": True,
            "filtered_documents": filtered,
            "count": len(filtered),
            "original_count": len(documents),
            "removed": len(documents) - len(filtered),
            "estimated_tokens": total_tokens,
            "similarity_threshold": similarity_threshold,
            "method": "filter_redundant"
        }

    def _sliding_window(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create sliding windows of context for long documents"""
        documents = params.get("documents", [])
        window_size = params.get("window_size", 512)  # tokens per window
        overlap = params.get("overlap", 128)  # token overlap between windows

        # Simulated sliding window
        # In production, would use proper tokenization
        windows = []

        for doc_idx, doc in enumerate(documents):
            words = doc.split()
            # Approximate: 1 token ≈ 0.75 words
            words_per_window = int(window_size * 0.75)
            words_overlap = int(overlap * 0.75)
            stride = words_per_window - words_overlap

            start = 0
            window_idx = 0

            while start < len(words):
                end = min(start + words_per_window, len(words))
                window_text = ' '.join(words[start:end])

                windows.append({
                    "window_id": f"doc{doc_idx}_win{window_idx}",
                    "document_index": doc_idx,
                    "window_index": window_idx,
                    "text": window_text,
                    "start_word": start,
                    "end_word": end,
                    "estimated_tokens": int((end - start) * 1.3)
                })

                window_idx += 1
                start += stride

                if end >= len(words):
                    break

        return {
            "success": True,
            "windows": windows,
            "count": len(windows),
            "window_size": window_size,
            "overlap": overlap,
            "method": "sliding_window"
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
