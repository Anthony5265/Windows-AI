"""
Postman API Testing Plugin
Provides API testing capabilities similar to Postman
"""

from typing import Dict, Any, Optional
import requests
import json


class PostmanPlugin:
    """Plugin for API testing similar to Postman"""

    name = "postman"
    version = "1.0.0"
    description = "API testing plugin with HTTP request capabilities"
    author = "Windows AI Team"

    def __init__(self):
        self.session = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Postman plugin"""
        try:
            self.session = requests.Session()
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Postman plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an API testing action"""
        if not self._initialized:
            return {"error": "Plugin not initialized"}

        try:
            if action == "send_request":
                return self._send_request(params)
            elif action == "get_request":
                return self._get_request(params)
            elif action == "post_request":
                return self._post_request(params)
            elif action == "put_request":
                return self._put_request(params)
            elif action == "delete_request":
                return self._delete_request(params)
            else:
                return {"error": f"Unknown action: {action}"}
        except Exception as e:
            return {"error": str(e)}

    def _send_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a custom HTTP request"""
        method = params.get("method", "GET").upper()
        url = params.get("url")
        headers = params.get("headers", {})
        data = params.get("data")
        json_data = params.get("json")

        if not url:
            return {"error": "URL parameter required"}

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                json=json_data
            )

            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text,
                "json": response.json() if response.headers.get('content-type', '').startswith('application/json') else None
            }
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

    def _get_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send GET request"""
        params["method"] = "GET"
        return self._send_request(params)

    def _post_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send POST request"""
        params["method"] = "POST"
        return self._send_request(params)

    def _put_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send PUT request"""
        params["method"] = "PUT"
        return self._send_request(params)

    def _delete_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send DELETE request"""
        params["method"] = "DELETE"
        return self._send_request(params)

    def cleanup(self):
        """Cleanup resources"""
        if self.session:
            self.session.close()
        self.session = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = PostmanPlugin
PLUGIN_NAME = "postman"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "API testing plugin with HTTP request capabilities"
PLUGIN_ACTIONS = [
    "send_request", "get_request", "post_request", "put_request", "delete_request"
]