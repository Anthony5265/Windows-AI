"""
RAG (Retrieval-Augmented Generation) Framework
Document processing, chunking, embedding, and semantic search
"""
from typing import Dict, Any, List, Optional
import logging
import re

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Process and chunk documents for RAG"""

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """Chunk text into overlapping segments"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = " ".join(words[i:i + self.chunk_size])
            chunks.append(chunk)

        return chunks

    def chunk_by_sentences(self, text: str, max_sentences: int = 5) -> List[str]:
        """Chunk text by sentences"""
        sentences = re.split(r'[.!?]+', text)
        chunks = []

        for i in range(0, len(sentences), max_sentences):
            chunk = ". ".join(sentences[i:i + max_sentences])
            if chunk:
                chunks.append(chunk.strip())

        return chunks

    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from text"""
        return {
            "length": len(text),
            "word_count": len(text.split()),
            "has_code": bool(re.search(r'```|def |class ', text)),
            "has_urls": bool(re.search(r'https?://', text))
        }


class RAGPipeline:
    """Complete RAG pipeline for semantic search"""

    def __init__(self, vector_db, embedding_model):
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        self.processor = DocumentProcessor()

    async def index_documents(self, collection_name: str, documents: List[str]) -> Dict[str, Any]:
        """Index documents for retrieval"""
        try:
            # Chunk documents
            all_chunks = []
            chunk_metadata = []

            for doc_id, doc in enumerate(documents):
                chunks = self.processor.chunk_text(doc)
                metadata = self.processor.extract_metadata(doc)

                for chunk_id, chunk in enumerate(chunks):
                    all_chunks.append(chunk)
                    chunk_metadata.append({
                        "doc_id": doc_id,
                        "chunk_id": chunk_id,
                        "text": chunk,
                        **metadata
                    })

            # Generate embeddings
            embeddings = await self.embedding_model.embed(all_chunks)

            # Store in vector database
            await self.vector_db.add(
                collection_name=collection_name,
                documents=all_chunks,
                embeddings=embeddings,
                metadatas=chunk_metadata
            )

            return {
                "status": "success",
                "indexed": len(documents),
                "chunks": len(all_chunks)
            }
        except Exception as e:
            logger.error(f"Index documents error: {e}")
            return {"status": "error", "message": str(e)}

    async def retrieve(self, collection_name: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieve relevant documents"""
        try:
            # Generate query embedding
            query_embedding = await self.embedding_model.embed([query])

            # Search vector database
            results = await self.vector_db.query(
                collection_name=collection_name,
                query_embeddings=query_embedding,
                n_results=top_k
            )

            return {
                "status": "success",
                "results": results
            }
        except Exception as e:
            logger.error(f"Retrieve error: {e}")
            return {"status": "error", "message": str(e)}

    async def generate_answer(self, query: str, context: List[str], llm_model) -> Dict[str, Any]:
        """Generate answer using retrieved context"""
        try:
            # Combine context
            combined_context = "\n\n".join(context)

            # Create prompt
            prompt = f"""Based on the following context, answer the question.

Context:
{combined_context}

Question: {query}

Answer:"""

            # Generate response
            response = await llm_model.complete(prompt=prompt)

            return {
                "status": "success",
                "answer": response,
                "context_used": len(context)
            }
        except Exception as e:
            logger.error(f"Generate answer error: {e}")
            return {"status": "error", "message": str(e)}
