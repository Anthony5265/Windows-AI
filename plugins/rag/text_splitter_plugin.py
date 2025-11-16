"""
Text Splitter Plugin
Intelligent text chunking for RAG
"""

from typing import Dict, Any, Optional, List


class TextSplitterPlugin:
    """Plugin for splitting text into chunks"""

    name = "text_splitter"
    version = "1.0.0"
    description = "Split text into chunks with overlap for RAG"
    author = "Windows AI Team"

    def __init__(self):
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Text Splitter plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Text Splitter plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a text splitting action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "character_split":
                return self._character_split(params)
            elif action == "recursive_split":
                return self._recursive_split(params)
            elif action == "sentence_split":
                return self._sentence_split(params)
            elif action == "semantic_split":
                return self._semantic_split(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _character_split(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Split text by character count"""
        text = params.get("text", "")
        chunk_size = params.get("chunk_size", 1000)
        chunk_overlap = params.get("chunk_overlap", 200)

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append({
                "text": chunk,
                "start": start,
                "end": min(end, len(text))
            })
            start = end - chunk_overlap

        return {
            "success": True,
            "chunks": chunks,
            "count": len(chunks)
        }

    def _recursive_split(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively split text on separators"""
        text = params.get("text", "")
        chunk_size = params.get("chunk_size", 1000)
        chunk_overlap = params.get("chunk_overlap", 200)
        separators = params.get("separators", ["\n\n", "\n", ". ", " ", ""])

        def split_text_recursive(text: str, separators: List[str]) -> List[str]:
            if not separators:
                return [text]

            separator = separators[0]
            splits = text.split(separator)

            chunks = []
            current_chunk = ""

            for split in splits:
                if len(current_chunk) + len(split) <= chunk_size:
                    current_chunk += split + separator
                else:
                    if current_chunk:
                        chunks.append(current_chunk.rstrip(separator))
                    current_chunk = split + separator

            if current_chunk:
                chunks.append(current_chunk.rstrip(separator))

            # If chunks are still too large, try next separator
            final_chunks = []
            for chunk in chunks:
                if len(chunk) > chunk_size and len(separators) > 1:
                    final_chunks.extend(split_text_recursive(chunk, separators[1:]))
                else:
                    final_chunks.append(chunk)

            return final_chunks

        chunk_texts = split_text_recursive(text, separators)
        chunks = [{"text": chunk, "index": i} for i, chunk in enumerate(chunk_texts)]

        return {
            "success": True,
            "chunks": chunks,
            "count": len(chunks)
        }

    def _sentence_split(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Split text by sentences"""
        import nltk

        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

        text = params.get("text", "")
        sentences_per_chunk = params.get("sentences_per_chunk", 5)

        sentences = nltk.sent_tokenize(text)
        chunks = []

        for i in range(0, len(sentences), sentences_per_chunk):
            chunk_sentences = sentences[i:i + sentences_per_chunk]
            chunks.append({
                "text": " ".join(chunk_sentences),
                "sentence_count": len(chunk_sentences),
                "index": i // sentences_per_chunk
            })

        return {
            "success": True,
            "chunks": chunks,
            "count": len(chunks)
        }

    def _semantic_split(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Split text based on semantic similarity"""
        from sentence_transformers import SentenceTransformer
        import numpy as np

        text = params.get("text", "")
        model_name = params.get("model", "all-MiniLM-L6-v2")
        threshold = params.get("threshold", 0.5)

        model = SentenceTransformer(model_name)

        # Split into sentences
        import nltk
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

        sentences = nltk.sent_tokenize(text)
        embeddings = model.encode(sentences)

        # Group sentences by similarity
        chunks = []
        current_chunk = [sentences[0]]

        for i in range(1, len(sentences)):
            similarity = np.dot(embeddings[i-1], embeddings[i])
            if similarity > threshold:
                current_chunk.append(sentences[i])
            else:
                chunks.append({
                    "text": " ".join(current_chunk),
                    "sentence_count": len(current_chunk)
                })
                current_chunk = [sentences[i]]

        if current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "sentence_count": len(current_chunk)
            })

        return {
            "success": True,
            "chunks": chunks,
            "count": len(chunks)
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        return True
