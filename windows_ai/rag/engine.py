"""
RAG Query Engine with Re-ranking and Context Retrieval
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import asyncio

logger = logging.getLogger(__name__)


class RerankStrategy(Enum):
    """Re-ranking strategies"""
    NONE = "none"
    MMR = "mmr"  # Maximal Marginal Relevance
    CROSS_ENCODER = "cross_encoder"
    LLM_RERANK = "llm_rerank"


@dataclass
class RAGConfig:
    """Configuration for RAG engine"""
    index_name: str
    top_k: int = 10
    rerank_top_k: int = 5
    rerank_strategy: RerankStrategy = RerankStrategy.NONE
    mmr_lambda: float = 0.5  # Balance between relevance and diversity
    use_hybrid_search: bool = False
    hybrid_alpha: float = 0.7  # Weight for vector vs keyword search
    context_window: int = 3  # Number of surrounding chunks to include
    include_metadata: bool = True


@dataclass
class RetrievalResult:
    """Result from document retrieval"""
    content: str
    score: float
    metadata: Dict[str, Any]
    chunk_id: Optional[int] = None
    document_hash: Optional[str] = None


@dataclass
class RAGResponse:
    """Response from RAG query"""
    query: str
    answer: str
    sources: List[RetrievalResult]
    context_used: str
    total_tokens: Optional[int] = None
    retrieval_time: Optional[float] = None
    generation_time: Optional[float] = None


class Reranker:
    """Re-ranking algorithms for search results"""

    @staticmethod
    def mmr_rerank(
        query_embedding: List[float],
        results: List[RetrievalResult],
        embeddings: List[List[float]],
        lambda_param: float = 0.5,
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        Maximal Marginal Relevance re-ranking.
        Balances relevance with diversity.

        Args:
            query_embedding: Query vector
            results: Search results
            embeddings: Embeddings for each result
            lambda_param: Balance between relevance (1.0) and diversity (0.0)
            top_k: Number of results to return

        Returns:
            Re-ranked results
        """
        import numpy as np

        if len(results) == 0:
            return []

        selected = []
        remaining_indices = list(range(len(results)))
        remaining_embeddings = embeddings.copy()

        query_vec = np.array(query_embedding)

        for _ in range(min(top_k, len(results))):
            if not remaining_indices:
                break

            mmr_scores = []

            for idx, emb in zip(remaining_indices, remaining_embeddings):
                # Relevance score (similarity to query)
                relevance = np.dot(query_vec, emb) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(emb)
                )

                # Diversity score (max similarity to already selected)
                if selected:
                    selected_embs = [embeddings[s_idx] for s_idx in selected]
                    max_similarity = max(
                        np.dot(emb, s_emb) / (np.linalg.norm(emb) * np.linalg.norm(s_emb))
                        for s_emb in selected_embs
                    )
                    diversity = 1 - max_similarity
                else:
                    diversity = 1.0

                # MMR score
                mmr_score = lambda_param * relevance + (1 - lambda_param) * diversity
                mmr_scores.append((idx, mmr_score))

            # Select best MMR score
            best_idx, best_score = max(mmr_scores, key=lambda x: x[1])
            selected.append(best_idx)
            remaining_indices.remove(best_idx)
            remaining_embeddings.remove(embeddings[best_idx])

        return [results[idx] for idx in selected]

    @staticmethod
    async def cross_encoder_rerank(
        query: str,
        results: List[RetrievalResult],
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        Re-rank using a cross-encoder model.

        Args:
            query: Query text
            results: Search results
            model_name: Cross-encoder model name
            top_k: Number of results to return

        Returns:
            Re-ranked results
        """
        try:
            from sentence_transformers import CrossEncoder
            model = CrossEncoder(model_name)

            # Create pairs for scoring
            pairs = [[query, result.content] for result in results]

            # Score pairs
            scores = model.predict(pairs)

            # Sort by score
            scored_results = list(zip(results, scores))
            scored_results.sort(key=lambda x: x[1], reverse=True)

            # Update scores and return top-k
            reranked = []
            for result, score in scored_results[:top_k]:
                result.score = float(score)
                reranked.append(result)

            return reranked

        except ImportError:
            logger.error("sentence-transformers not installed for cross-encoder")
            return results[:top_k]
        except Exception as e:
            logger.error(f"Cross-encoder reranking error: {e}")
            return results[:top_k]


class ContextBuilder:
    """Builds context from retrieved chunks"""

    @staticmethod
    def build_context(
        results: List[RetrievalResult],
        max_tokens: int = 4000,
        include_metadata: bool = True
    ) -> str:
        """
        Build context string from results.

        Args:
            results: Retrieved results
            max_tokens: Maximum tokens for context
            include_metadata: Include metadata in context

        Returns:
            Context string
        """
        context_parts = []
        current_tokens = 0

        for i, result in enumerate(results):
            # Rough token estimation (4 chars ≈ 1 token)
            estimated_tokens = len(result.content) // 4

            if current_tokens + estimated_tokens > max_tokens:
                break

            # Format result
            part = f"[Source {i+1}]\n{result.content}"

            if include_metadata and result.metadata:
                file_name = result.metadata.get('file_name', 'Unknown')
                part += f"\n(Source: {file_name})"

            context_parts.append(part)
            current_tokens += estimated_tokens

        return "\n\n".join(context_parts)

    @staticmethod
    def expand_context(
        results: List[RetrievalResult],
        all_chunks: Dict[str, List[Dict[str, Any]]],
        window_size: int = 3
    ) -> List[RetrievalResult]:
        """
        Expand results with surrounding chunks.

        Args:
            results: Retrieved results
            all_chunks: All chunks indexed by document_hash
            window_size: Number of chunks before/after to include

        Returns:
            Expanded results
        """
        expanded = []

        for result in results:
            if not result.document_hash or not result.chunk_id:
                expanded.append(result)
                continue

            doc_chunks = all_chunks.get(result.document_hash, [])

            # Get surrounding chunks
            start_idx = max(0, result.chunk_id - window_size)
            end_idx = min(len(doc_chunks), result.chunk_id + window_size + 1)

            surrounding = doc_chunks[start_idx:end_idx]

            # Merge content
            merged_content = "\n\n".join(chunk['content'] for chunk in surrounding)

            expanded_result = RetrievalResult(
                content=merged_content,
                score=result.score,
                metadata=result.metadata,
                chunk_id=result.chunk_id,
                document_hash=result.document_hash
            )

            expanded.append(expanded_result)

        return expanded


class RAGEngine:
    """Complete RAG engine with retrieval and generation"""

    def __init__(
        self,
        vector_db,
        embedding_model,
        llm_model=None,
        config: Optional[RAGConfig] = None
    ):
        """
        Initialize RAG engine.

        Args:
            vector_db: Vector database instance
            embedding_model: Embedding model instance
            llm_model: Optional LLM for generation
            config: RAG configuration
        """
        self.vector_db = vector_db
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.config = config or RAGConfig(index_name="default")
        self.reranker = Reranker()
        self.context_builder = ContextBuilder()

    async def index_documents(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Index documents into vector database.

        Args:
            documents: List of documents with 'content' and 'metadata'
            batch_size: Batch size for indexing

        Returns:
            Indexing result
        """
        try:
            # Extract content
            texts = [doc['content'] for doc in documents]
            metadatas = [doc.get('metadata', {}) for doc in documents]

            # Generate embeddings
            logger.info(f"Generating embeddings for {len(texts)} documents...")
            embeddings = await self.embedding_model.embed(texts)

            # Generate IDs
            ids = [f"doc_{i}" for i in range(len(documents))]

            # Upsert to vector database
            logger.info(f"Upserting to vector database...")
            result = await self.vector_db.batch_upsert(
                index_name=self.config.index_name,
                vectors=embeddings,
                ids=ids,
                metadata=metadatas,
                documents=texts,
                batch_size=batch_size
            )

            return result

        except Exception as e:
            logger.error(f"Document indexing error: {e}")
            return {"status": "error", "message": str(e)}

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        rerank: bool = True
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant documents for query.

        Args:
            query: Query text
            top_k: Number of results (uses config default if not provided)
            rerank: Whether to apply re-ranking

        Returns:
            List of retrieval results
        """
        import time

        start_time = time.time()
        top_k = top_k or self.config.top_k

        try:
            # Generate query embedding
            query_embedding = await self.embedding_model.embed(query)

            # Search vector database
            if self.config.use_hybrid_search and hasattr(self.vector_db, 'search_hybrid'):
                # Hybrid search (vector + keyword)
                search_result = await self.vector_db.search_hybrid(
                    index_name=self.config.index_name,
                    query_text=query,
                    query_vector=query_embedding,
                    top_k=top_k * 2 if rerank else top_k,  # Get more for reranking
                    alpha=self.config.hybrid_alpha
                )
            else:
                # Pure vector search
                search_result = await self.vector_db.search(
                    index_name=self.config.index_name,
                    query_vector=query_embedding,
                    top_k=top_k * 2 if rerank else top_k,
                    include_metadata=self.config.include_metadata
                )

            if search_result.get('status') != 'success':
                logger.error(f"Search failed: {search_result.get('message')}")
                return []

            # Convert to RetrievalResult
            results = [
                RetrievalResult(
                    content=r.document or "",
                    score=r.score,
                    metadata=r.metadata or {},
                    chunk_id=r.metadata.get('chunk_id') if r.metadata else None,
                    document_hash=r.metadata.get('document_hash') if r.metadata else None
                )
                for r in search_result.get('results', [])
            ]

            # Apply re-ranking
            if rerank and self.config.rerank_strategy != RerankStrategy.NONE:
                if self.config.rerank_strategy == RerankStrategy.MMR:
                    # Get embeddings for results
                    result_embeddings = await self.embedding_model.embed(
                        [r.content for r in results]
                    )
                    results = self.reranker.mmr_rerank(
                        query_embedding=query_embedding,
                        results=results,
                        embeddings=result_embeddings,
                        lambda_param=self.config.mmr_lambda,
                        top_k=self.config.rerank_top_k
                    )
                elif self.config.rerank_strategy == RerankStrategy.CROSS_ENCODER:
                    results = await self.reranker.cross_encoder_rerank(
                        query=query,
                        results=results,
                        top_k=self.config.rerank_top_k
                    )

            retrieval_time = time.time() - start_time
            logger.info(f"Retrieved {len(results)} results in {retrieval_time:.2f}s")

            return results[:top_k]

        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

    async def query(
        self,
        query: str,
        system_prompt: Optional[str] = None
    ) -> RAGResponse:
        """
        Complete RAG query with retrieval and generation.

        Args:
            query: User query
            system_prompt: Optional system prompt for generation

        Returns:
            RAG response with answer and sources
        """
        import time

        # Retrieve relevant documents
        results = await self.retrieve(query)

        if not results:
            return RAGResponse(
                query=query,
                answer="I couldn't find any relevant information to answer your query.",
                sources=[],
                context_used=""
            )

        # Build context
        context = self.context_builder.build_context(
            results,
            include_metadata=self.config.include_metadata
        )

        # Generate answer if LLM available
        answer = ""
        generation_time = None

        if self.llm_model:
            start_time = time.time()

            # Create prompt
            if not system_prompt:
                system_prompt = "You are a helpful assistant. Answer the question based on the provided context. If the context doesn't contain enough information, say so."

            prompt = f"""{system_prompt}

Context:
{context}

Question: {query}

Answer:"""

            # Generate response
            try:
                # Assuming LLM has a complete() or generate() method
                if hasattr(self.llm_model, 'complete'):
                    answer = await self.llm_model.complete(prompt)
                elif hasattr(self.llm_model, 'generate'):
                    answer = await self.llm_model.generate(prompt)
                else:
                    answer = "LLM model doesn't support generation"

                generation_time = time.time() - start_time
            except Exception as e:
                logger.error(f"Generation error: {e}")
                answer = f"Error generating answer: {str(e)}"
        else:
            # Return context if no LLM
            answer = "Retrieved relevant information (no LLM configured for generation):\n\n" + context

        return RAGResponse(
            query=query,
            answer=answer,
            sources=results,
            context_used=context,
            generation_time=generation_time
        )

    async def query_stream(self, query: str, system_prompt: Optional[str] = None):
        """
        Stream RAG response (for real-time generation).

        Args:
            query: User query
            system_prompt: Optional system prompt

        Yields:
            Response chunks
        """
        # Retrieve relevant documents
        results = await self.retrieve(query)

        if not results:
            yield {
                "type": "error",
                "message": "No relevant documents found"
            }
            return

        # Send sources first
        yield {
            "type": "sources",
            "sources": [
                {
                    "content": r.content[:200] + "...",
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in results
            ]
        }

        # Build context
        context = self.context_builder.build_context(results)

        # Stream answer if LLM supports streaming
        if self.llm_model and hasattr(self.llm_model, 'stream'):
            if not system_prompt:
                system_prompt = "You are a helpful assistant. Answer based on the provided context."

            prompt = f"""{system_prompt}

Context:
{context}

Question: {query}

Answer:"""

            async for chunk in self.llm_model.stream(prompt):
                yield {
                    "type": "content",
                    "content": chunk
                }
        else:
            # Non-streaming fallback
            response = await self.query(query, system_prompt)
            yield {
                "type": "content",
                "content": response.answer
            }

        yield {
            "type": "done"
        }
