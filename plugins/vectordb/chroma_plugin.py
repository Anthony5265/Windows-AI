"""
ChromaDB Plugin
Open-source embedding database for RAG
"""

from typing import Dict, Any, Optional, List


class ChromaDBPlugin:
    """Plugin for ChromaDB vector database"""

    name = "chromadb"
    version = "1.0.0"
    description = "Integration with ChromaDB for vector storage and retrieval"
    author = "Windows AI Team"

    def __init__(self):
        self.client = None
        self.collection = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the ChromaDB plugin"""
        try:
            import chromadb

            persist_directory = config.get("persist_directory", "./chroma_db") if config else "./chroma_db"

            self.client = chromadb.PersistentClient(path=persist_directory)
            self._initialized = True
            return True
        except ImportError:
            print("chromadb package not installed. Install with: pip install chromadb")
            return False
        except Exception as e:
            print(f"Error initializing ChromaDB plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a ChromaDB action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_collection":
                return self._create_collection(params)
            elif action == "add_documents":
                return self._add_documents(params)
            elif action == "query":
                return self._query(params)
            elif action == "delete":
                return self._delete(params)
            elif action == "list_collections":
                return self._list_collections()
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collection"""
        name = params.get("name", "default")
        metadata = params.get("metadata", {})

        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata=metadata
        )

        return {
            "success": True,
            "collection_name": name
        }

    def _add_documents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add documents to collection"""
        documents = params.get("documents", [])
        metadatas = params.get("metadatas", [])
        ids = params.get("ids", [f"doc_{i}" for i in range(len(documents))])

        if not self.collection:
            return {"success": False, "error": "No collection selected"}

        self.collection.add(
            documents=documents,
            metadatas=metadatas if metadatas else None,
            ids=ids
        )

        return {
            "success": True,
            "added": len(documents)
        }

    def _query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query collection"""
        query_texts = params.get("query_texts", [])
        n_results = params.get("n_results", 5)
        where = params.get("where", None)

        if not self.collection:
            return {"success": False, "error": "No collection selected"}

        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where
        )

        return {
            "success": True,
            "results": results
        }

    def _delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete documents"""
        ids = params.get("ids", [])

        if not self.collection:
            return {"success": False, "error": "No collection selected"}

        self.collection.delete(ids=ids)

        return {
            "success": True,
            "deleted": len(ids)
        }

    def _list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        collections = self.client.list_collections()

        return {
            "success": True,
            "collections": [col.name for col in collections]
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        self.collection = None
        return True
