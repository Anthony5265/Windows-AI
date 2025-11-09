"""
LangChain RAG Plugin
Provides Retrieval-Augmented Generation capabilities using LangChain framework
"""

from typing import Dict, Any, Optional, List
import os


class LangChainPlugin:
    """Plugin for LangChain-based RAG applications"""

    name = "langchain_rag"
    version = "1.0.0"
    description = "Retrieval-Augmented Generation using LangChain"
    author = "Windows AI Team"

    def __init__(self):
        self.vectorstore = None
        self.chain = None
        self.embeddings = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the LangChain RAG plugin"""
        try:
            # Import LangChain components
            from langchain_community.vectorstores import FAISS
            from langchain_openai import OpenAIEmbeddings, ChatOpenAI
            from langchain.chains import RetrievalQA
            from langchain.text_splitter import RecursiveCharacterTextSplitter

            # Get configuration
            openai_api_key = (
                config.get("openai_api_key") if config
                else os.getenv("OPENAI_API_KEY")
            )

            if not openai_api_key:
                print("OpenAI API key not provided. Set OPENAI_API_KEY environment variable or provide in config.")
                return False

            # Initialize embeddings
            self.embeddings = OpenAIEmbeddings(api_key=openai_api_key)

            # Initialize LLM
            llm = ChatOpenAI(api_key=openai_api_key, model="gpt-3.5-turbo")

            # Store for later use
            self.llm = llm
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )

            self._initialized = True
            return True

        except ImportError as e:
            print(f"Missing dependencies: {e}. Install with: pip install langchain langchain-openai langchain-community faiss-cpu")
            return False
        except Exception as e:
            print(f"Error initializing LangChain plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a LangChain RAG action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide OpenAI API key."}

        try:
            if action == "load_documents":
                return self._load_documents(params)
            elif action == "create_vectorstore":
                return self._create_vectorstore(params)
            elif action == "query":
                return self._query(params)
            elif action == "add_documents":
                return self._add_documents(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _load_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load documents from various sources"""
        try:
            from langchain_community.document_loaders import TextLoader, DirectoryLoader

            source_type = params.get("source_type", "text")
            source_path = params.get("source_path")

            if not source_path:
                return {"error": "source_path is required"}

            if source_type == "text":
                loader = TextLoader(source_path)
                documents = loader.load()
            elif source_type == "directory":
                loader = DirectoryLoader(source_path, glob="**/*.txt")
                documents = loader.load()
            else:
                return {"error": f"Unsupported source_type: {source_type}"}

            # Split documents
            split_docs = self.text_splitter.split_documents(documents)

            return {
                "documents": [
                    {"content": doc.page_content, "metadata": doc.metadata}
                    for doc in split_docs
                ],
                "count": len(split_docs)
            }

        except Exception as e:
            return {"error": f"Failed to load documents: {str(e)}"}

    def _create_vectorstore(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create vector store from documents"""
        try:
            from langchain_community.vectorstores import FAISS

            documents_data = params.get("documents", [])
            if not documents_data:
                return {"error": "documents are required"}

            # Convert to Document objects
            from langchain_core.documents import Document
            documents = [
                Document(page_content=doc["content"], metadata=doc.get("metadata", {}))
                for doc in documents_data
            ]

            # Create vector store
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)

            # Create retrieval chain
            self.chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever()
            )

            return {
                "status": "Vector store created successfully",
                "document_count": len(documents)
            }

        except Exception as e:
            return {"error": f"Failed to create vector store: {str(e)}"}

    def _query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query the RAG system"""
        if not self.chain:
            return {"error": "Vector store not created. Call create_vectorstore first."}

        try:
            query = params.get("query")
            if not query:
                return {"error": "query is required"}

            # Get relevant documents
            docs = self.vectorstore.similarity_search(query, k=3)
            relevant_docs = [
                {"content": doc.page_content, "metadata": doc.metadata}
                for doc in docs
            ]

            # Generate answer
            result = self.chain.invoke({"query": query})

            return {
                "answer": result["result"],
                "relevant_documents": relevant_docs,
                "source_count": len(relevant_docs)
            }

        except Exception as e:
            return {"error": f"Failed to query: {str(e)}"}

    def _add_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add new documents to existing vector store"""
        if not self.vectorstore:
            return {"error": "Vector store not created. Call create_vectorstore first."}

        try:
            documents_data = params.get("documents", [])
            if not documents_data:
                return {"error": "documents are required"}

            # Convert to Document objects
            from langchain_core.documents import Document
            documents = [
                Document(page_content=doc["content"], metadata=doc.get("metadata", {}))
                for doc in documents_data
            ]

            # Add to vector store
            self.vectorstore.add_documents(documents)

            return {
                "status": "Documents added successfully",
                "added_count": len(documents)
            }

        except Exception as e:
            return {"error": f"Failed to add documents: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.vectorstore = None
        self.chain = None
        self.embeddings = None
        self.llm = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = LangChainPlugin
PLUGIN_NAME = "langchain_rag"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Retrieval-Augmented Generation using LangChain"
PLUGIN_ACTIONS = ["load_documents", "create_vectorstore", "query", "add_documents"]