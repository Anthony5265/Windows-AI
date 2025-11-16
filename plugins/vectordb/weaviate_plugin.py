"""
Weaviate Plugin
Open-source vector database with GraphQL API
"""

from typing import Dict, Any, Optional, List
import os


class WeaviatePlugin:
    """Plugin for Weaviate vector database"""

    name = "weaviate"
    version = "1.0.0"
    description = "Integration with Weaviate for vector search and storage"
    author = "Windows AI Team"

    def __init__(self):
        self.client = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Weaviate plugin"""
        try:
            import weaviate

            url = config.get("url", "http://localhost:8080") if config else "http://localhost:8080"
            api_key = config.get("api_key") if config else os.getenv("WEAVIATE_API_KEY")

            if api_key:
                self.client = weaviate.Client(
                    url=url,
                    auth_client_secret=weaviate.AuthApiKey(api_key=api_key)
                )
            else:
                self.client = weaviate.Client(url=url)

            self._initialized = True
            return True
        except ImportError:
            print("weaviate-client package not installed. Install with: pip install weaviate-client")
            return False
        except Exception as e:
            print(f"Error initializing Weaviate plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Weaviate action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "create_schema":
                return self._create_schema(params)
            elif action == "add_objects":
                return self._add_objects(params)
            elif action == "query":
                return self._query(params)
            elif action == "vector_search":
                return self._vector_search(params)
            elif action == "delete":
                return self._delete(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_schema(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create schema for a class"""
        class_obj = params.get("class_obj", {})

        self.client.schema.create_class(class_obj)

        return {
            "success": True,
            "class_name": class_obj.get("class", "")
        }

    def _add_objects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add objects to collection"""
        class_name = params.get("class_name", "")
        objects = params.get("objects", [])

        with self.client.batch as batch:
            for obj in objects:
                batch.add_data_object(obj, class_name)

        return {
            "success": True,
            "added": len(objects)
        }

    def _query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query objects using GraphQL"""
        class_name = params.get("class_name", "")
        properties = params.get("properties", ["*"])
        limit = params.get("limit", 10)
        where_filter = params.get("where", None)

        query = self.client.query.get(class_name, properties).with_limit(limit)

        if where_filter:
            query = query.with_where(where_filter)

        results = query.do()

        return {
            "success": True,
            "results": results
        }

    def _vector_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform vector similarity search"""
        class_name = params.get("class_name", "")
        vector = params.get("vector", [])
        properties = params.get("properties", ["*"])
        limit = params.get("limit", 5)

        results = (
            self.client.query
            .get(class_name, properties)
            .with_near_vector({"vector": vector})
            .with_limit(limit)
            .do()
        )

        return {
            "success": True,
            "results": results
        }

    def _delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete objects"""
        class_name = params.get("class_name", "")
        where_filter = params.get("where", {})

        self.client.batch.delete_objects(
            class_name=class_name,
            where=where_filter
        )

        return {
            "success": True
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.client = None
        return True
