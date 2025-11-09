"""
Qdrant Vector Database Plugin
Supports vector similarity search and storage operations
"""

from typing import Dict, Any, Optional, List
import os


class QdrantPlugin:
    """Plugin for Qdrant vector database operations"""
    
    name = "qdrant"
    version = "1.0.0"
    description = "Integration with Qdrant vector database"
    author = "Windows AI Team"
    
    def __init__(self):
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Qdrant plugin"""
        try:
            from qdrant_client import QdrantClient
            
            # Get connection parameters from config or environment
            host = (
                config.get("host") if config 
                else os.getenv("QDRANT_HOST", "localhost")
            )
            port = (
                config.get("port") if config 
                else int(os.getenv("QDRANT_PORT", "6333"))
            )
            api_key = (
                config.get("api_key") if config 
                else os.getenv("QDRANT_API_KEY")
            )
            https = (
                config.get("https", False) if config 
                else os.getenv("QDRANT_HTTPS", "false").lower() == "true"
            )
            
            # Initialize client
            if api_key:
                self.client = QdrantClient(
                    host=host,
                    port=port,
                    api_key=api_key,
                    https=https
                )
            else:
                self.client = QdrantClient(host=host, port=port, https=https)
            
            # Test connection
            self.client.get_collections()
            self._initialized = True
            return True
            
        except ImportError:
            print("qdrant-client package not installed. Install with: pip install qdrant-client")
            return False
        except Exception as e:
            print(f"Error initializing Qdrant plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Qdrant action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please check connection parameters."}
        
        try:
            if action == "create_collection":
                return self._create_collection(params)
            elif action == "delete_collection":
                return self._delete_collection(params)
            elif action == "list_collections":
                return self._list_collections()
            elif action == "get_collection_info":
                return self._get_collection_info(params)
            elif action == "upsert_vectors":
                return self._upsert_vectors(params)
            elif action == "search":
                return self._search(params)
            elif action == "delete_vectors":
                return self._delete_vectors(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _create_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}
        
        vector_size = params.get("vector_size", 768)
        distance = params.get("distance", "Cosine")
        
        try:
            from qdrant_client.models import Distance, VectorParams
            
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance[distance])
            )
            
            return {
                "success": True,
                "collection_name": collection_name,
                "vector_size": vector_size,
                "distance": distance
            }
            
        except Exception as e:
            return {"error": f"Failed to create collection: {str(e)}"}
    
    def _delete_collection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}
        
        try:
            self.client.delete_collection(collection_name=collection_name)
            return {"success": True, "collection_name": collection_name}
            
        except Exception as e:
            return {"error": f"Failed to delete collection: {str(e)}"}
    
    def _list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        try:
            collections = self.client.get_collections()
            return {
                "collections": [col.name for col in collections.collections],
                "count": len(collections.collections)
            }
            
        except Exception as e:
            return {"error": f"Failed to list collections: {str(e)}"}
    
    def _get_collection_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get collection information"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}
        
        try:
            info = self.client.get_collection(collection_name=collection_name)
            return {
                "collection_name": collection_name,
                "status": info.status,
                "vector_count": info.vectors_count,
                "points_count": info.points_count,
                "config": {
                    "params": info.config.params.__dict__ if info.config.params else None,
                    "vectors": info.config.vectors.__dict__ if info.config.vectors else None
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to get collection info: {str(e)}"}
    
    def _upsert_vectors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert vectors into collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}
        
        points = params.get("points", [])
        if not points:
            return {"error": "points array is required"}
        
        try:
            from qdrant_client.models import PointStruct
            
            # Convert points to PointStruct if needed
            qdrant_points = []
            for point in points:
                if isinstance(point, dict):
                    qdrant_points.append(PointStruct(
                        id=point.get("id"),
                        vector=point.get("vector"),
                        payload=point.get("payload", {})
                    ))
                else:
                    qdrant_points.append(point)
            
            result = self.client.upsert(
                collection_name=collection_name,
                points=qdrant_points
            )
            
            return {
                "success": True,
                "operation_id": result.operation_id,
                "status": result.status
            }
            
        except Exception as e:
            return {"error": f"Failed to upsert vectors: {str(e)}"}
    
    def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for similar vectors"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}
        
        query_vector = params.get("query_vector")
        if not query_vector:
            return {"error": "query_vector is required"}
        
        limit = params.get("limit", 10)
        score_threshold = params.get("score_threshold")
        
        try:
            search_params = {"limit": limit}
            if score_threshold is not None:
                search_params["score_threshold"] = score_threshold
            
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                **search_params
            )
            
            # Convert results to dict
            hits = []
            for hit in results:
                hits.append({
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload,
                    "vector": hit.vector
                })
            
            return {
                "results": hits,
                "count": len(hits)
            }
            
        except Exception as e:
            return {"error": f"Failed to search: {str(e)}"}
    
    def _delete_vectors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete vectors from collection"""
        collection_name = params.get("collection_name")
        if not collection_name:
            return {"error": "collection_name is required"}
        
        point_ids = params.get("point_ids", [])
        if not point_ids:
            return {"error": "point_ids array is required"}
        
        try:
            from qdrant_client.models import PointIdsList
            
            result = self.client.delete(
                collection_name=collection_name,
                points_selector=PointIdsList(points=point_ids)
            )
            
            return {
                "success": True,
                "operation_id": result.operation_id,
                "status": result.status
            }
            
        except Exception as e:
            return {"error": f"Failed to delete vectors: {str(e)}"}
    
    def cleanup(self):
        """Cleanup resources"""
        if self.client:
            self.client.close()
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = QdrantPlugin
PLUGIN_NAME = "qdrant"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Qdrant vector database"
PLUGIN_ACTIONS = ["create_collection", "delete_collection", "list_collections", "get_collection_info", "upsert_vectors", "search", "delete_vectors"]