"""
Grafana DevOps Plugin
Supports Grafana dashboard management, monitoring, and alerting through Grafana API
"""

from typing import Dict, Any, Optional, List
import os
import requests
import json


class GrafanaPlugin:
    """Plugin for Grafana dashboard and monitoring management"""

    name = "grafana"
    version = "1.0.0"
    description = "Integration with Grafana API for dashboard management and monitoring"
    author = "Windows AI Team"

    def __init__(self):
        self.base_url: Optional[str] = None
        self.api_key: Optional[str] = None
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Grafana plugin"""
        try:
            # Get configuration
            self.base_url = (
                config.get("base_url") if config
                else os.getenv("GRAFANA_URL", "http://localhost:3000")
            )

            self.api_key = (
                config.get("api_key") if config
                else os.getenv("GRAFANA_API_KEY")
            )

            self.username = (
                config.get("username") if config
                else os.getenv("GRAFANA_USERNAME")
            )

            self.password = (
                config.get("password") if config
                else os.getenv("GRAFANA_PASSWORD")
            )

            if not self.base_url:
                print("Grafana base URL not provided")
                return False

            if not self.api_key and not (self.username and self.password):
                print("Grafana credentials not provided. Set GRAFANA_API_KEY or GRAFANA_USERNAME/GRAFANA_PASSWORD")
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing Grafana plugin: {e}")
            return False

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers

    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to Grafana API"""
        try:
            url = f"{self.base_url}/api{endpoint}"
            headers = self._get_headers()
            auth = None

            # Use basic auth if no API key
            if not self.api_key and self.username and self.password:
                auth = (self.username, self.password)

            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, auth=auth)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, auth=auth)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, auth=auth)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, auth=auth)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}

            if response.status_code in [200, 201, 202, 204]:
                try:
                    return response.json() if response.content else {}
                except:
                    return {}
            else:
                return {"error": f"API request failed: {response.status_code} - {response.text}"}

        except Exception as e:
            return {"error": str(e)}

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Grafana action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please configure Grafana credentials."}

        try:
            if action == "list_dashboards":
                return self._list_dashboards(params)
            elif action == "get_dashboard":
                return self._get_dashboard(params)
            elif action == "create_dashboard":
                return self._create_dashboard(params)
            elif action == "update_dashboard":
                return self._update_dashboard(params)
            elif action == "delete_dashboard":
                return self._delete_dashboard(params)
            elif action == "list_datasources":
                return self._list_datasources(params)
            elif action == "create_datasource":
                return self._create_datasource(params)
            elif action == "get_alerts":
                return self._get_alerts(params)
            elif action == "create_alert":
                return self._create_alert(params)
            elif action == "get_health":
                return self._get_health(params)
            elif action == "search":
                return self._search(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _list_dashboards(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all dashboards"""
        query_params = {}
        
        if params.get("limit"):
            query_params["limit"] = params["limit"]
        if params.get("tag"):
            query_params["tag"] = params["tag"]
        if params.get("type"):
            query_params["type"] = params["type"]

        result = self._make_request("/search", params=query_params)

        if "error" in result:
            return result

        return {
            "dashboards": result,
            "count": len(result) if isinstance(result, list) else 0
        }

    def _get_dashboard(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific dashboard"""
        uid = params.get("uid")
        dashboard_id = params.get("id")

        if not uid and not dashboard_id:
            return {"error": "Dashboard UID or ID is required"}

        if uid:
            endpoint = f"/dashboards/uid/{uid}"
        else:
            endpoint = f"/dashboards/id/{dashboard_id}"

        result = self._make_request(endpoint)

        if "error" in result:
            return result

        return {"dashboard": result}

    def _create_dashboard(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new dashboard"""
        dashboard = params.get("dashboard")
        folder_id = params.get("folder_id", 0)
        overwrite = params.get("overwrite", False)

        if not dashboard:
            return {"error": "Dashboard configuration is required"}

        payload = {
            "dashboard": dashboard,
            "folderId": folder_id,
            "overwrite": overwrite
        }

        result = self._make_request("/dashboards/db", "POST", payload)

        if "error" in result:
            return result

        return {
            "success": True,
            "dashboard": result,
            "message": "Dashboard created successfully"
        }

    def _update_dashboard(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing dashboard"""
        dashboard = params.get("dashboard")
        folder_id = params.get("folder_id", 0)
        overwrite = params.get("overwrite", True)

        if not dashboard:
            return {"error": "Dashboard configuration is required"}

        if not dashboard.get("uid"):
            return {"error": "Dashboard UID is required for updates"}

        payload = {
            "dashboard": dashboard,
            "folderId": folder_id,
            "overwrite": overwrite
        }

        result = self._make_request("/dashboards/db", "POST", payload)

        if "error" in result:
            return result

        return {
            "success": True,
            "dashboard": result,
            "message": "Dashboard updated successfully"
        }

    def _delete_dashboard(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a dashboard"""
        uid = params.get("uid")

        if not uid:
            return {"error": "Dashboard UID is required"}

        result = self._make_request(f"/dashboards/uid/{uid}", "DELETE")

        if "error" in result:
            return result

        return {
            "success": True,
            "message": f"Dashboard {uid} deleted successfully"
        }

    def _list_datasources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all datasources"""
        result = self._make_request("/datasources")

        if "error" in result:
            return result

        return {
            "datasources": result,
            "count": len(result) if isinstance(result, list) else 0
        }

    def _create_datasource(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new datasource"""
        datasource_config = params.get("datasource")

        if not datasource_config:
            return {"error": "Datasource configuration is required"}

        result = self._make_request("/datasources", "POST", datasource_config)

        if "error" in result:
            return result

        return {
            "success": True,
            "datasource": result,
            "message": "Datasource created successfully"
        }

    def _get_alerts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get alerts"""
        query_params = {}
        
        if params.get("state"):
            query_params["state"] = params["state"]
        if params.get("limit"):
            query_params["limit"] = params["limit"]

        result = self._make_request("/alerts", params=query_params)

        if "error" in result:
            return result

        return {
            "alerts": result,
            "count": len(result) if isinstance(result, list) else 0
        }

    def _create_alert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an alert"""
        alert_config = params.get("alert")

        if not alert_config:
            return {"error": "Alert configuration is required"}

        result = self._make_request("/alerts", "POST", alert_config)

        if "error" in result:
            return result

        return {
            "success": True,
            "alert": result,
            "message": "Alert created successfully"
        }

    def _get_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Grafana health status"""
        result = self._make_request("/health")

        if "error" in result:
            return result

        return {"health": result}

    def _search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for dashboards, panels, etc."""
        query = params.get("query", "")
        search_type = params.get("type", "dash-db")  # dash-db, dash-folder, etc.
        tag = params.get("tag")
        limit = params.get("limit", 1000)

        query_params = {
            "query": query,
            "type": search_type,
            "limit": limit
        }

        if tag:
            query_params["tag"] = tag

        result = self._make_request("/search", params=query_params)

        if "error" in result:
            return result

        return {
            "results": result,
            "count": len(result) if isinstance(result, list) else 0
        }

    def cleanup(self):
        """Cleanup resources"""
        self.base_url = None
        self.api_key = None
        self.username = None
        self.password = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = GrafanaPlugin
PLUGIN_NAME = "grafana"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Grafana API for dashboard management and monitoring"
PLUGIN_ACTIONS = [
    "list_dashboards", "get_dashboard", "create_dashboard", "update_dashboard", "delete_dashboard",
    "list_datasources", "create_datasource", "get_alerts", "create_alert", "get_health", "search"
]