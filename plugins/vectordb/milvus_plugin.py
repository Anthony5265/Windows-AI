"""
Milvus Plugin
Open-source vector database built for scalable similarity search
"""

from typing import Dict, Any, Optional, List


class MilvusPlugin:
    """Plugin for Milvus vector database"""

    name = "milvus"
    version = "1.0.0"
    description = "Integration with Milvus for scalable vector search"
    author = "Windows AI Team"

    def __init__(self):
        self.connections = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Milvus plugin"""
        try:
            from pymilvus import connections

            host = config.get("host", "localhost") if config else "localhost"
            port = config.get("port", "19530") if config else "19530"
            alias = config.get("alias", "default") if config else "default"

            connections.connect(alias=alias, host=host, port=port)
            self.connections = connections
            self._initialized = True
            return True
        except ImportError:
            print("pymilvus package not installed. Install with: pip install pymilvus")
            return False
        except Exception as e:
            print(f"Error initializing Milvus plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Milvus action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_collection":
                return self._create_collection(params)
            elif action == "insert":
                return self._insert(params)
            elif action == "search":
                return self._search(params)
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
        from pymilvus import CollectionSchema, FieldSchema, DataType, Collection

        collection_name = params.get("collection_name", "")
        dimension = params.get("dimension", 1536)

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535)
        ]

        schema = CollectionSchema(fields=fields, description="Document collection")
        collection = Collection(name=collection_name, schema=schema)

        # Create index
        index_params = {
            "metric_type": "L2",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
        collection.create_index(field_name="embedding", index_params=index_params)

        return {
            "success": True,
            "collection_name": collection_name
        }

    def _insert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Insert vectors"""
        from pymilvus import Collection

        collection_name = params.get("collection_name", "")
        embeddings = params.get("embeddings", [])
        texts = params.get("texts", [])

        collection = Collection(collection_name)
        entities = [embeddings, texts]

        collection.insert(entities)
        collection.flush()

        return {
            "success": True,
            "inserted": len(embeddings)
        }

    def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for similar vectors"""
        from pymilvus import Collection

        collection_name = params.get("collection_name", "")
        query_vectors = params.get("query_vectors", [])
        top_k = params.get("top_k", 5)

        collection = Collection(collection_name)
        collection.load()

        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = collection.search(
            data=query_vectors,
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            output_fields=["text"]
        )

        return {
            "success": True,
            "results": [
                {
                    "id": hit.id,
                    "distance": hit.distance,
                    "text": hit.entity.get("text")
                }
                for hits in results for hit in hits
            ]
        }

    def _delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete vectors"""
        from pymilvus import Collection

        collection_name = params.get("collection_name", "")
        expr = params.get("expr", "")

        collection = Collection(collection_name)
        collection.delete(expr)

        return {
            "success": True
        }

    def _list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        from pymilvus import utility

        collections = utility.list_collections()

        return {
            "success": True,
            "collections": collections
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        if self.connections:
            self.connections.disconnect("default")
        self._initialized = False
        return True
