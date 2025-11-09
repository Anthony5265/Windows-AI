"""
LlamaIndex RAG Plugin
Provides Retrieval-Augmented Generation capabilities using LlamaIndex framework
"""

from typing import Dict, Any, Optional, List
import os
import logging


class LlamaIndexPlugin:
    """Plugin for LlamaIndex-based RAG applications"""

    name = "llamaindex_rag"
    version = "1.0.0"
    description = "Retrieval-Augmented Generation using LlamaIndex"
    author = "Windows AI Team"

    def __init__(self):
        self.index = None
        self.query_engine = None
        self.documents = []
        self._initialized = False
        self.logger = logging.getLogger(__name__)

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the LlamaIndex RAG plugin"""
        try:
            # Import LlamaIndex components
            from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document
            from llama_index.core.node_parser import SimpleNodeParser
            from llama_index.embeddings.openai import OpenAIEmbedding
            from llama_index.llms.openai import OpenAI

            # Get configuration
            openai_api_key = (
                config.get("openai_api_key") if config
                else os.getenv("OPENAI_API_KEY")
            )

            if not openai_api_key:
                self.logger.error("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or provide in config.")
                return False

            # Initialize OpenAI components
            self.llm = OpenAI(api_key=openai_api_key, model="gpt-3.5-turbo")
            self.embed_model = OpenAIEmbedding(api_key=openai_api_key)

            # Initialize node parser for document splitting
            self.node_parser = SimpleNodeParser.from_defaults(
                chunk_size=1024,
                chunk_overlap=200
            )

            self._initialized = True
            self.logger.info("LlamaIndex plugin initialized successfully")
            return True

        except ImportError as e:
            self.logger.error(f"Missing dependencies: {e}. Install with: pip install llama-index llama-index-embeddings-openai llama-index-llms-openai")
            return False
        except Exception as e:
            self.logger.error(f"Error initializing LlamaIndex plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a LlamaIndex RAG action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide OpenAI API key."}

        try:
            if action == "load_documents":
                return self._load_documents(params)
            elif action == "create_index":
                return self._create_index(params)
            elif action == "query":
                return self._query(params)
            elif action == "add_documents":
                return self._add_documents(params)
            elif action == "save_index":
                return self._save_index(params)
            elif action == "load_index":
                return self._load_index(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {"error": str(e)}

    def _load_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load documents from various sources"""
        try:
            from llama_index.core import SimpleDirectoryReader, Document

            source_type = params.get("source_type", "text")
            source_path = params.get("source_path")
            source_content = params.get("source_content")

            if not source_path and not source_content:
                return {"error": "Either source_path or source_content is required"}

            documents = []

            if source_type == "text" and source_content:
                # Load from text content
                documents = [Document(text=source_content)]
            elif source_type == "file" and source_path:
                # Load from single file
                if not os.path.exists(source_path):
                    return {"error": f"File not found: {source_path}"}
                documents = SimpleDirectoryReader(input_files=[source_path]).load_data()
            elif source_type == "directory" and source_path:
                # Load from directory
                if not os.path.exists(source_path):
                    return {"error": f"Directory not found: {source_path}"}
                documents = SimpleDirectoryReader(source_path).load_data()
            else:
                return {"error": f"Unsupported source_type: {source_type}"}

            # Store documents
            self.documents.extend(documents)

            return {
                "documents_loaded": len(documents),
                "total_documents": len(self.documents),
                "status": "Documents loaded successfully"
            }

        except Exception as e:
            self.logger.error(f"Failed to load documents: {e}")
            return {"error": f"Failed to load documents: {str(e)}"}

    def _create_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create vector store index from loaded documents"""
        try:
            from llama_index.core import VectorStoreIndex

            if not self.documents:
                return {"error": "No documents loaded. Call load_documents first."}

            # Create index
            self.index = VectorStoreIndex(
                self.documents,
                embed_model=self.embed_model,
                node_parser=self.node_parser
            )

            # Create query engine
            self.query_engine = self.index.as_query_engine(
                llm=self.llm,
                similarity_top_k=params.get("similarity_top_k", 3)
            )

            return {
                "status": "Index created successfully",
                "document_count": len(self.documents),
                "index_type": "VectorStoreIndex"
            }

        except Exception as e:
            self.logger.error(f"Failed to create index: {e}")
            return {"error": f"Failed to create index: {str(e)}"}

    def _query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query the RAG system"""
        if not self.query_engine:
            return {"error": "Index not created. Call create_index first."}

        try:
            query = params.get("query")
            if not query:
                return {"error": "query is required"}

            # Execute query
            response = self.query_engine.query(query)

            # Get source nodes (retrieved documents)
            source_nodes = []
            if hasattr(response, 'source_nodes'):
                source_nodes = [
                    {
                        "content": node.node.text,
                        "score": node.score,
                        "metadata": node.node.metadata
                    }
                    for node in response.source_nodes
                ]

            return {
                "answer": str(response),
                "relevant_documents": source_nodes,
                "source_count": len(source_nodes)
            }

        except Exception as e:
            self.logger.error(f"Failed to query: {e}")
            return {"error": f"Failed to query: {str(e)}"}

    def _add_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add new documents to existing index"""
        if not self.index:
            return {"error": "Index not created. Call create_index first."}

        try:
            from llama_index.core import Document

            documents_data = params.get("documents", [])
            if not documents_data:
                return {"error": "documents are required"}

            # Convert to Document objects
            new_documents = []
            for doc_data in documents_data:
                if isinstance(doc_data, dict):
                    text = doc_data.get("content", doc_data.get("text", ""))
                    metadata = doc_data.get("metadata", {})
                    new_documents.append(Document(text=text, metadata=metadata))
                elif isinstance(doc_data, str):
                    new_documents.append(Document(text=doc_data))

            if not new_documents:
                return {"error": "No valid documents provided"}

            # Add to index
            for doc in new_documents:
                self.index.insert(doc)

            # Update stored documents
            self.documents.extend(new_documents)

            # Refresh query engine
            self.query_engine = self.index.as_query_engine(llm=self.llm)

            return {
                "status": "Documents added successfully",
                "added_count": len(new_documents),
                "total_documents": len(self.documents)
            }

        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            return {"error": f"Failed to add documents: {str(e)}"}

    def _save_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Save index to disk"""
        if not self.index:
            return {"error": "Index not created. Call create_index first."}

        try:
            persist_dir = params.get("persist_dir", "./llamaindex_index")
            if not persist_dir:
                return {"error": "persist_dir is required"}

            # Create directory if it doesn't exist
            os.makedirs(persist_dir, exist_ok=True)

            # Save index
            self.index.storage_context.persist(persist_dir=persist_dir)

            return {
                "status": "Index saved successfully",
                "persist_dir": persist_dir
            }

        except Exception as e:
            self.logger.error(f"Failed to save index: {e}")
            return {"error": f"Failed to save index: {str(e)}"}

    def _load_index(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load index from disk"""
        try:
            from llama_index.core import load_index_from_storage, StorageContext

            persist_dir = params.get("persist_dir", "./llamaindex_index")
            if not persist_dir or not os.path.exists(persist_dir):
                return {"error": f"Persist directory not found: {persist_dir}"}

            # Load index
            storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
            self.index = load_index_from_storage(storage_context)

            # Create query engine
            self.query_engine = self.index.as_query_engine(llm=self.llm)

            return {
                "status": "Index loaded successfully",
                "persist_dir": persist_dir
            }

        except Exception as e:
            self.logger.error(f"Failed to load index: {e}")
            return {"error": f"Failed to load index: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.index = None
        self.query_engine = None
        self.documents = []
        self.llm = None
        self.embed_model = None
        self.node_parser = None
        self._initialized = False
        self.logger.info("LlamaIndex plugin cleaned up")


# Plugin metadata
PLUGIN_CLASS = LlamaIndexPlugin
PLUGIN_NAME = "llamaindex_rag"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Retrieval-Augmented Generation using LlamaIndex"
PLUGIN_ACTIONS = ["load_documents", "create_index", "query", "add_documents", "save_index", "load_index"]