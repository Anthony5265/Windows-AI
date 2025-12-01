"""
RAG API Endpoints
FastAPI routes for document indexing and querying
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import asyncio
import json
from pathlib import Path
import tempfile
import os

from .engine import RAGEngine, RAGConfig, RerankStrategy
from ..embeddings import get_embedding_model, EmbeddingProvider
from ..document_processor import DocumentProcessor, ChunkStrategy, ChunkConfig
from ..vector_db import VectorDBManager

logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(prefix="/rag", tags=["RAG"])

# Global state (would be better in dependency injection)
_rag_engines: Dict[str, RAGEngine] = {}
_vector_db_manager = VectorDBManager()


# Request/Response Models

class IndexDocumentsRequest(BaseModel):
    """Request to index documents"""
    collection_name: str = Field(..., description="Name of the collection")
    documents: List[str] = Field(..., description="List of document texts")
    metadata: Optional[List[Dict[str, Any]]] = Field(None, description="Metadata for each document")
    chunk_strategy: str = Field("fixed_size", description="Chunking strategy")
    chunk_size: int = Field(512, description="Size of chunks")
    chunk_overlap: int = Field(50, description="Overlap between chunks")
    embedding_provider: str = Field("openai", description="Embedding provider")
    vector_db_provider: str = Field("chroma", description="Vector database provider")


class IndexFileRequest(BaseModel):
    """Request to index files from directory"""
    collection_name: str
    directory_path: str
    recursive: bool = True
    file_patterns: Optional[List[str]] = None
    chunk_strategy: str = "semantic"
    chunk_size: int = 512
    embedding_provider: str = "openai"
    vector_db_provider: str = "chroma"


class QueryRequest(BaseModel):
    """Request to query RAG system"""
    collection_name: str
    query: str
    top_k: int = Field(5, ge=1, le=50)
    rerank: bool = True
    rerank_strategy: str = "mmr"
    use_hybrid_search: bool = False
    system_prompt: Optional[str] = None


class QueryResponse(BaseModel):
    """Response from RAG query"""
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    retrieval_time: Optional[float] = None
    generation_time: Optional[float] = None


class CollectionInfo(BaseModel):
    """Information about a collection"""
    name: str
    vector_count: int
    dimension: int
    metadata: Dict[str, Any]


class IndexingStatus(BaseModel):
    """Status of indexing operation"""
    collection_name: str
    status: str
    documents_processed: int
    chunks_created: int
    message: Optional[str] = None


# Helper Functions

def get_or_create_rag_engine(
    collection_name: str,
    embedding_provider: str = "openai",
    vector_db_provider: str = "chroma",
    rerank_strategy: str = "none"
) -> RAGEngine:
    """Get or create RAG engine for collection"""
    engine_key = f"{collection_name}:{embedding_provider}:{vector_db_provider}"

    if engine_key in _rag_engines:
        return _rag_engines[engine_key]

    # Create embedding model
    embedding_model = get_embedding_model(embedding_provider)

    # Create vector database
    vector_db = _vector_db_manager.get_provider(vector_db_provider)

    # Create RAG config
    rag_config = RAGConfig(
        index_name=collection_name,
        rerank_strategy=RerankStrategy(rerank_strategy),
        top_k=10
    )

    # Create RAG engine
    engine = RAGEngine(
        vector_db=vector_db,
        embedding_model=embedding_model,
        config=rag_config
    )

    _rag_engines[engine_key] = engine
    return engine


async def process_and_index_documents(
    collection_name: str,
    documents: List[Dict[str, Any]],
    chunk_config: ChunkConfig,
    embedding_provider: str,
    vector_db_provider: str
) -> Dict[str, Any]:
    """Process and index documents"""
    try:
        # Create document processor
        processor = DocumentProcessor(chunk_config)

        # Process documents
        all_chunks = []
        for doc_data in documents:
            content = doc_data.get('content', '')
            metadata = doc_data.get('metadata', {})

            from ..document_processor import Document
            doc = Document(content=content, metadata=metadata)

            chunks = processor.chunker.chunk(content, doc)
            all_chunks.extend(chunks)

        logger.info(f"Created {len(all_chunks)} chunks from {len(documents)} documents")

        # Prepare for indexing
        chunk_documents = []
        for chunk in all_chunks:
            chunk_documents.append({
                'content': chunk.content,
                'metadata': chunk.metadata
            })

        # Get RAG engine
        engine = get_or_create_rag_engine(
            collection_name,
            embedding_provider,
            vector_db_provider
        )

        # Index documents
        result = await engine.index_documents(chunk_documents)

        return {
            "status": "success",
            "collection_name": collection_name,
            "documents_processed": len(documents),
            "chunks_created": len(all_chunks),
            "indexing_result": result
        }

    except Exception as e:
        logger.error(f"Error processing and indexing documents: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# API Endpoints

@router.post("/index", response_model=IndexingStatus)
async def index_documents(request: IndexDocumentsRequest, background_tasks: BackgroundTasks):
    """
    Index documents into a collection.

    This endpoint chunks documents, generates embeddings, and stores them in a vector database.
    """
    try:
        # Create chunk config
        chunk_config = ChunkConfig(
            strategy=ChunkStrategy(request.chunk_strategy),
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )

        # Prepare documents
        documents = []
        for i, doc_text in enumerate(request.documents):
            doc_data = {
                'content': doc_text,
                'metadata': request.metadata[i] if request.metadata and i < len(request.metadata) else {}
            }
            documents.append(doc_data)

        # Process and index
        result = await process_and_index_documents(
            collection_name=request.collection_name,
            documents=documents,
            chunk_config=chunk_config,
            embedding_provider=request.embedding_provider,
            vector_db_provider=request.vector_db_provider
        )

        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result.get('message', 'Indexing failed'))

        return IndexingStatus(
            collection_name=request.collection_name,
            status="success",
            documents_processed=result['documents_processed'],
            chunks_created=result['chunks_created']
        )

    except Exception as e:
        logger.error(f"Index documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/files")
async def index_files(request: IndexFileRequest, background_tasks: BackgroundTasks):
    """
    Index files from a directory.

    Recursively processes supported file formats (PDF, DOCX, TXT, MD, etc.)
    and indexes them into the specified collection.
    """
    try:
        # Validate directory
        directory = Path(request.directory_path)
        if not directory.exists() or not directory.is_dir():
            raise HTTPException(status_code=400, detail="Invalid directory path")

        # Create chunk config
        chunk_config = ChunkConfig(
            strategy=ChunkStrategy(request.chunk_strategy),
            chunk_size=request.chunk_size
        )

        # Create document processor
        processor = DocumentProcessor(chunk_config)

        # Process directory
        results = processor.process_directory(
            directory_path=str(directory),
            recursive=request.recursive,
            file_patterns=request.file_patterns
        )

        # Prepare documents for indexing
        documents = []
        for doc, chunks in results:
            for chunk in chunks:
                documents.append({
                    'content': chunk.content,
                    'metadata': chunk.metadata
                })

        # Index documents
        result = await process_and_index_documents(
            collection_name=request.collection_name,
            documents=documents,
            chunk_config=chunk_config,
            embedding_provider=request.embedding_provider,
            vector_db_provider=request.vector_db_provider
        )

        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result.get('message'))

        return {
            "status": "success",
            "collection_name": request.collection_name,
            "files_processed": len(results),
            "chunks_indexed": len(documents)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Index files error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryResponse)
async def query_collection(request: QueryRequest):
    """
    Query a collection with semantic search and optional generation.

    Returns relevant documents and optionally generates an answer using an LLM.
    """
    try:
        # Get RAG engine
        engine = get_or_create_rag_engine(
            collection_name=request.collection_name,
            rerank_strategy=request.rerank_strategy
        )

        # Update config for this query
        engine.config.top_k = request.top_k
        engine.config.use_hybrid_search = request.use_hybrid_search

        # Execute query
        result = await engine.query(
            query=request.query,
            system_prompt=request.system_prompt
        )

        # Format sources
        sources = [
            {
                "content": source.content,
                "score": source.score,
                "metadata": source.metadata
            }
            for source in result.sources
        ]

        return QueryResponse(
            query=result.query,
            answer=result.answer,
            sources=sources,
            retrieval_time=result.retrieval_time,
            generation_time=result.generation_time
        )

    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query/stream")
async def query_collection_stream(
    collection_name: str,
    query: str,
    top_k: int = 5,
    rerank: bool = True
):
    """
    Stream query results for real-time generation.

    Returns a streaming response with sources first, then generated content.
    """
    try:
        engine = get_or_create_rag_engine(collection_name)

        async def generate():
            async for chunk in engine.query_stream(query):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )

    except Exception as e:
        logger.error(f"Query stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collections", response_model=List[CollectionInfo])
async def list_collections(vector_db_provider: str = "chroma"):
    """
    List all available collections in the vector database.
    """
    try:
        vector_db = _vector_db_manager.get_provider(vector_db_provider)

        # Connect if needed
        if not getattr(vector_db, '_connected', False):
            await vector_db.connect()

        # List indexes
        result = await vector_db.list_indexes()

        if result.get('status') != 'success':
            raise HTTPException(status_code=500, detail="Failed to list collections")

        collections = []
        for index_name in result.get('indexes', []):
            # Get stats for each index
            stats_result = await vector_db.get_index_stats(index_name)

            if stats_result.get('status') == 'success':
                stats = stats_result['stats']
                collections.append(CollectionInfo(
                    name=stats.name,
                    vector_count=stats.total_vectors,
                    dimension=stats.dimension,
                    metadata=stats.metadata or {}
                ))

        return collections

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List collections error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str, vector_db_provider: str = "chroma"):
    """
    Delete a collection from the vector database.
    """
    try:
        vector_db = _vector_db_manager.get_provider(vector_db_provider)

        # Connect if needed
        if not getattr(vector_db, '_connected', False):
            await vector_db.connect()

        # Delete index
        result = await vector_db.delete_index(collection_name)

        if result.get('status') != 'success':
            raise HTTPException(status_code=500, detail=result.get('message', 'Delete failed'))

        # Remove from cache
        engine_keys = [k for k in _rag_engines.keys() if k.startswith(f"{collection_name}:")]
        for key in engine_keys:
            del _rag_engines[key]

        return {
            "status": "success",
            "message": f"Collection '{collection_name}' deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete collection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_and_index(
    collection_name: str,
    file: UploadFile = File(...),
    chunk_strategy: str = "semantic",
    embedding_provider: str = "openai",
    vector_db_provider: str = "chroma"
):
    """
    Upload a file and index its contents.

    Supports PDF, DOCX, TXT, MD, JSON, CSV, and HTML files.
    """
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            # Process file
            chunk_config = ChunkConfig(strategy=ChunkStrategy(chunk_strategy))
            processor = DocumentProcessor(chunk_config)

            doc, chunks = processor.process_file(tmp_path)

            # Prepare for indexing
            documents = []
            for chunk in chunks:
                documents.append({
                    'content': chunk.content,
                    'metadata': chunk.metadata
                })

            # Index
            result = await process_and_index_documents(
                collection_name=collection_name,
                documents=documents,
                chunk_config=chunk_config,
                embedding_provider=embedding_provider,
                vector_db_provider=vector_db_provider
            )

            if result['status'] == 'error':
                raise HTTPException(status_code=500, detail=result.get('message'))

            return {
                "status": "success",
                "file_name": file.filename,
                "chunks_indexed": len(chunks)
            }

        finally:
            # Clean up temp file
            os.unlink(tmp_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload and index error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Check health of RAG system"""
    return {
        "status": "healthy",
        "active_engines": len(_rag_engines),
        "available_providers": _vector_db_manager.list_providers()
    }
