"""
RAG Pipeline Manager - Complete Retrieval Augmented Generation
Document loading, chunking, embedding, retrieval, generation
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Document:
    content: str
    metadata: Dict[str, Any]
    id: Optional[str] = None

@dataclass
class Chunk:
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class RAGPipelineManager:
    """Complete RAG pipeline with multiple strategies"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True

    # ==================== DOCUMENT LOADING ====================

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    async def load_documents(self, source: str, source_type: str = "file") -> List[Document]:
        """Load documents from various sources"""
        if source_type == "file":
            return await self._load_file(source)
        elif source_type == "directory":
            return await self._load_directory(source)
        elif source_type == "url":
            return await self._load_url(source)
        elif source_type == "pdf":
            return await self._load_pdf(source)
        elif source_type == "github":
            return await self._load_github(source)
        elif source_type == "notion":
            return await self._load_notion(source)
        elif source_type == "confluence":
            return await self._load_confluence(source)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    async def _load_file(self, path: str) -> List[Document]:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return [Document(content=content, metadata={"source": path, "type": "file"})]

    async def _load_directory(self, path: str) -> List[Document]:
        documents = []
        for file_path in Path(path).rglob("*"):
            if file_path.is_file() and file_path.suffix in [".txt", ".md", ".py", ".js", ".html", ".json"]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    documents.append(Document(
                        content=content,
                        metadata={"source": str(file_path), "type": "file"}
                    ))
                except:
                    pass
        return documents

    async def _load_url(self, url: str) -> List[Document]:
        import aiohttp
        from bs4 import BeautifulSoup

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator="\n", strip=True)

        return [Document(content=text, metadata={"source": url, "type": "url"})]

    async def _load_pdf(self, path: str) -> List[Document]:
        import pypdf

        reader = pypdf.PdfReader(path)
        documents = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                documents.append(Document(
                    content=text,
                    metadata={"source": path, "type": "pdf", "page": i + 1}
                ))
        return documents

    async def _load_github(self, repo: str) -> List[Document]:
        import aiohttp

        documents = []
        api_url = f"https://api.github.com/repos/{repo}/contents"
        headers = {"Authorization": f"token {os.environ.get('GITHUB_TOKEN')}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, headers=headers) as response:
                files = await response.json()

            for file in files:
                if file["type"] == "file" and file["name"].endswith((".md", ".txt", ".py")):
                    async with session.get(file["download_url"]) as resp:
                        content = await resp.text()
                        documents.append(Document(
                            content=content,
                            metadata={"source": file["path"], "type": "github", "repo": repo}
                        ))

        return documents

    async def _load_notion(self, page_id: str) -> List[Document]:
        import aiohttp

        api_key = os.environ.get("NOTION_API_KEY")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers=headers
            ) as response:
                data = await response.json()

        text_blocks = []
        for block in data.get("results", []):
            if block["type"] == "paragraph":
                texts = block.get("paragraph", {}).get("rich_text", [])
                text_blocks.append("".join([t["plain_text"] for t in texts]))

        return [Document(
            content="\n".join(text_blocks),
            metadata={"source": page_id, "type": "notion"}
        )]

    async def _load_confluence(self, page_id: str) -> List[Document]:
        import aiohttp
        from bs4 import BeautifulSoup

        base_url = os.environ.get("CONFLUENCE_URL")
        token = os.environ.get("CONFLUENCE_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{base_url}/rest/api/content/{page_id}?expand=body.storage",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                data = await response.json()

        html = data["body"]["storage"]["value"]
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        return [Document(content=text, metadata={"source": page_id, "type": "confluence"})]

    # ==================== CHUNKING ====================

    def chunk_documents(
        self,
        documents: List[Document],
        strategy: str = "recursive",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ) -> List[Chunk]:
        """Chunk documents using various strategies"""
        if strategy == "recursive":
            return self._recursive_chunk(documents, chunk_size, chunk_overlap)
        elif strategy == "semantic":
            return self._semantic_chunk(documents, chunk_size)
        elif strategy == "sentence":
            return self._sentence_chunk(documents, chunk_size, chunk_overlap)
        elif strategy == "fixed":
            return self._fixed_chunk(documents, chunk_size, chunk_overlap)
        else:
            raise ValueError(f"Unsupported chunking strategy: {strategy}")

    def _recursive_chunk(self, documents, chunk_size, chunk_overlap):
        separators = ["\n\n", "\n", ". ", " ", ""]
        chunks = []

        for doc in documents:
            text = doc.content
            for sep in separators:
                if len(text) <= chunk_size:
                    break
                parts = text.split(sep)
                current_chunk = ""
                for part in parts:
                    if len(current_chunk) + len(part) + len(sep) <= chunk_size:
                        current_chunk += part + sep
                    else:
                        if current_chunk:
                            chunks.append(Chunk(content=current_chunk.strip(), metadata=doc.metadata.copy()))
                        current_chunk = part + sep
                if current_chunk:
                    text = current_chunk

            if text:
                chunks.append(Chunk(content=text.strip(), metadata=doc.metadata.copy()))

        return chunks

    def _sentence_chunk(self, documents, chunk_size, chunk_overlap):
        import re
        chunks = []

        for doc in documents:
            sentences = re.split(r'(?<=[.!?])\s+', doc.content)
            current_chunk = ""

            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= chunk_size:
                    current_chunk += " " + sentence
                else:
                    if current_chunk:
                        chunks.append(Chunk(content=current_chunk.strip(), metadata=doc.metadata.copy()))
                    current_chunk = sentence

            if current_chunk:
                chunks.append(Chunk(content=current_chunk.strip(), metadata=doc.metadata.copy()))

        return chunks

    def _fixed_chunk(self, documents, chunk_size, chunk_overlap):
        chunks = []
        for doc in documents:
            text = doc.content
            for i in range(0, len(text), chunk_size - chunk_overlap):
                chunk_text = text[i:i + chunk_size]
                if chunk_text:
                    chunks.append(Chunk(content=chunk_text, metadata=doc.metadata.copy()))
        return chunks

    def _semantic_chunk(self, documents, chunk_size):
        # Simplified semantic chunking based on paragraph structure
        chunks = []
        for doc in documents:
            paragraphs = doc.content.split("\n\n")
            current_chunk = ""
            for para in paragraphs:
                if len(current_chunk) + len(para) <= chunk_size:
                    current_chunk += "\n\n" + para
                else:
                    if current_chunk:
                        chunks.append(Chunk(content=current_chunk.strip(), metadata=doc.metadata.copy()))
                    current_chunk = para
            if current_chunk:
                chunks.append(Chunk(content=current_chunk.strip(), metadata=doc.metadata.copy()))
        return chunks

    # ==================== EMBEDDING & INDEXING ====================

    async def embed_chunks(
        self,
        chunks: List[Chunk],
        provider: str = "openai",
        model: str = None
    ) -> List[Chunk]:
        """Generate embeddings for chunks"""
        from windows_ai.integrations.embeddings import EmbeddingsManager, EmbeddingProvider

        embeddings_mgr = EmbeddingsManager()
        await embeddings_mgr.initialize()

        texts = [chunk.content for chunk in chunks]
        embeddings = await embeddings_mgr.embed(texts, EmbeddingProvider(provider), model)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        return chunks

    async def index_chunks(
        self,
        chunks: List[Chunk],
        collection_name: str,
        vector_store: str = "chromadb"
    ) -> bool:
        """Index chunks in vector store"""
        from windows_ai.integrations.vector_stores import VectorStoresManager, VectorStoreProvider

        store = VectorStoresManager()
        await store.initialize()

        await store.create_collection(collection_name, VectorStoreProvider(vector_store))

        documents = [chunk.content for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]

        return await store.add_documents(collection_name, documents, embeddings, metadatas, provider=VectorStoreProvider(vector_store))

    # ==================== RETRIEVAL ====================

    async def retrieve(
        self,
        query: str,
        collection_name: str,
        vector_store: str = "chromadb",
        top_k: int = 5,
        rerank: bool = False,
        rerank_provider: str = "cohere"
    ) -> List[Dict]:
        """Retrieve relevant chunks"""
        from windows_ai.integrations.embeddings import EmbeddingsManager, EmbeddingProvider
        from windows_ai.integrations.vector_stores import VectorStoresManager, VectorStoreProvider

        # Embed query
        embeddings_mgr = EmbeddingsManager()
        await embeddings_mgr.initialize()
        query_embedding = (await embeddings_mgr.embed(query))[0]

        # Search
        store = VectorStoresManager()
        await store.initialize()
        results = await store.search(collection_name, query_embedding, top_k=top_k * 2 if rerank else top_k, provider=VectorStoreProvider(vector_store))

        # Rerank if requested
        if rerank and results:
            documents = [r["document"] for r in results]
            reranked = await embeddings_mgr.rerank(query, documents, provider=rerank_provider, top_k=top_k)
            return reranked

        return results[:top_k]

    # ==================== GENERATION ====================

    async def generate(
        self,
        query: str,
        context: List[Dict],
        llm_provider: str = "openai",
        model: str = None,
        system_prompt: str = None
    ) -> str:
        """Generate response using retrieved context"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        context_text = "\n\n".join([
            f"Source: {c.get('metadata', {}).get('source', 'Unknown')}\n{c.get('document', c.get('content', ''))}"
            for c in context
        ])

        default_system = """You are a helpful assistant. Use the provided context to answer questions.
If the context doesn't contain the answer, say so. Always cite your sources."""

        messages = [
            {"role": "system", "content": f"{system_prompt or default_system}\n\nContext:\n{context_text}"},
            {"role": "user", "content": query}
        ]

        response = await ai.chat(Provider(llm_provider), messages, model=model)
        return response["content"]

    # ==================== FULL PIPELINE ====================

    async def query(
        self,
        query: str,
        collection_name: str,
        vector_store: str = "chromadb",
        llm_provider: str = "openai",
        top_k: int = 5,
        rerank: bool = True
    ) -> Dict[str, Any]:
        """Full RAG query pipeline"""
        context = await self.retrieve(query, collection_name, vector_store, top_k, rerank)
        response = await self.generate(query, context, llm_provider)
        return {
            "answer": response,
            "sources": context
        }

    async def ingest(
        self,
        source: str,
        source_type: str,
        collection_name: str,
        vector_store: str = "chromadb",
        chunk_strategy: str = "recursive",
        chunk_size: int = 1000
    ) -> int:
        """Full ingestion pipeline"""
        documents = await self.load_documents(source, source_type)
        chunks = self.chunk_documents(documents, chunk_strategy, chunk_size)
        chunks = await self.embed_chunks(chunks)
        await self.index_chunks(chunks, collection_name, vector_store)
        return len(chunks)
