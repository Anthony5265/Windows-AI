"""
LlamaIndex Integration for Windows AI
Advanced RAG and data indexing capabilities
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class LlamaIndexManager:
    """Manages LlamaIndex integration for advanced RAG"""

    def __init__(self):
        self.indexes: Dict[str, Any] = {}
        self.query_engines: Dict[str, Any] = {}
        self.agents: Dict[str, Any] = {}
        self._initialized = False

    async def initialize(self, config: Optional[Dict[str, Any]] = None):
        """Initialize LlamaIndex components"""
        if self._initialized:
            return

        try:
            from llama_index.core import Settings, VectorStoreIndex, SimpleDirectoryReader
            from llama_index.llms.openai import OpenAI
            from llama_index.embeddings.openai import OpenAIEmbedding

            # Configure global settings
            Settings.llm = OpenAI(model="gpt-4-turbo-preview", temperature=0.7)
            Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
            Settings.chunk_size = 1024
            Settings.chunk_overlap = 200

            self._initialized = True
            logger.info("LlamaIndex integration initialized successfully")

        except ImportError as e:
            logger.warning(f"LlamaIndex not fully available: {e}")

    async def create_index_from_documents(
        self,
        name: str,
        documents: List[str],
        index_type: str = "vector"
    ) -> Any:
        """Create an index from document texts"""
        from llama_index.core import VectorStoreIndex, Document
        from llama_index.core.node_parser import SentenceSplitter

        # Convert to Document objects
        docs = [Document(text=doc) for doc in documents]

        # Create parser
        parser = SentenceSplitter(chunk_size=1024, chunk_overlap=200)
        nodes = parser.get_nodes_from_documents(docs)

        # Create index
        if index_type == "vector":
            index = VectorStoreIndex(nodes)
        else:
            index = VectorStoreIndex(nodes)

        self.indexes[name] = index
        return index

    async def create_index_from_directory(
        self,
        name: str,
        directory_path: str,
        recursive: bool = True
    ) -> Any:
        """Create an index from a directory of documents"""
        from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

        reader = SimpleDirectoryReader(
            input_dir=directory_path,
            recursive=recursive
        )
        documents = reader.load_data()

        index = VectorStoreIndex.from_documents(documents)
        self.indexes[name] = index
        return index

    async def create_query_engine(
        self,
        name: str,
        index_name: str,
        similarity_top_k: int = 5,
        response_mode: str = "compact"
    ) -> Any:
        """Create a query engine from an index"""
        index = self.indexes.get(index_name)
        if not index:
            raise ValueError(f"Index '{index_name}' not found")

        query_engine = index.as_query_engine(
            similarity_top_k=similarity_top_k,
            response_mode=response_mode
        )

        self.query_engines[name] = query_engine
        return query_engine

    async def query(self, engine_name: str, query_text: str) -> str:
        """Query using a query engine"""
        engine = self.query_engines.get(engine_name)
        if not engine:
            raise ValueError(f"Query engine '{engine_name}' not found")

        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: engine.query(query_text)
        )
        return str(response)

    async def create_chat_engine(
        self,
        name: str,
        index_name: str,
        chat_mode: str = "condense_plus_context"
    ) -> Any:
        """Create a chat engine with memory"""
        from llama_index.core.memory import ChatMemoryBuffer

        index = self.indexes.get(index_name)
        if not index:
            raise ValueError(f"Index '{index_name}' not found")

        memory = ChatMemoryBuffer.from_defaults(token_limit=3900)

        chat_engine = index.as_chat_engine(
            chat_mode=chat_mode,
            memory=memory,
            verbose=True
        )

        return chat_engine

    async def create_agent(
        self,
        name: str,
        tools: Optional[List[Any]] = None,
        llm_model: str = "gpt-4-turbo-preview"
    ) -> Any:
        """Create a LlamaIndex agent"""
        from llama_index.core.agent import ReActAgent
        from llama_index.llms.openai import OpenAI
        from llama_index.core.tools import FunctionTool

        llm = OpenAI(model=llm_model)

        # Default tools if none provided
        if tools is None:
            def search_documents(query: str) -> str:
                """Search through indexed documents"""
                if self.query_engines:
                    engine = list(self.query_engines.values())[0]
                    return str(engine.query(query))
                return "No documents indexed yet"

            tools = [
                FunctionTool.from_defaults(fn=search_documents)
            ]

        agent = ReActAgent.from_tools(tools, llm=llm, verbose=True)
        self.agents[name] = agent
        return agent

    async def run_agent(self, name: str, query: str) -> str:
        """Run an agent with a query"""
        agent = self.agents.get(name)
        if not agent:
            raise ValueError(f"Agent '{name}' not found")

        response = await asyncio.get_event_loop().run_in_executor(
            None, lambda: agent.chat(query)
        )
        return str(response)

    def get_indexes(self) -> List[str]:
        """Get list of created indexes"""
        return list(self.indexes.keys())

    def get_query_engines(self) -> List[str]:
        """Get list of created query engines"""
        return list(self.query_engines.keys())
