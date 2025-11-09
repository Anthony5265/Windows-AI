"""
Sentry Plugin
Supports Sentry error monitoring, issue tracking, and performance management through Sentry API
"""

from typing import Dict, Any, Optional, List
import os
import requests
import json
from datetime import datetime, timedelta


class SentryPlugin:
    """Plugin for Sentry error monitoring and issue tracking"""

    name = "sentry"
    version = "1.0.0"
    description = "Integration with Sentry API for error monitoring and issue tracking"
    author = "Windows AI Team"

    def __init__(self):
        self.auth_token: Optional[str] = None
        self.base_url: Optional[str] = None
        self.organization_slug: Optional[str] = None
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Sentry plugin"""
        try:
            # Get configuration from config dict or environment variables
            self.auth_token = (
                config.get("auth_token") if config
                else os.getenv("SENTRY_AUTH_TOKEN")
            )
            
            self.base_url = (
                config.get("base_url") if config
                else os.getenv("SENTRY_BASE_URL", "https://sentry.io")
            )
            
            self.organization_slug = (
                config.get("organization_slug") if config
                else os.getenv("SENTRY_ORGANIZATION")
            )

            if not self.auth_token:
                print("Sentry auth token not provided. Set SENTRY_AUTH_TOKEN environment variable or provide auth_token in config.")
                return False

            if not self.organization_slug:
                print("Sentry organization slug not provided. Set SENTRY_ORGANIZATION environment variable or provide organization_slug in config.")
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing Sentry plugin: {e}")
            return False

    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to Sentry API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }

            url = f"{self.base_url}/api/0{endpoint}"

            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
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
        """Execute a Sentry action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide Sentry auth token and organization slug."}

        try:
            if action == "list_issues":
                return self._list_issues(params)
            elif action == "get_issue":
                return self._get_issue(params)
            elif action == "update_issue":
                return self._update_issue(params)
            elif action == "resolve_issue":
                return self._resolve_issue(params)
            elif action == "create_issue":
                return self._create_issue(params)
            elif action == "list_projects":
                return self._list_projects(params)
            elif action == "get_project":
                return self._get_project(params)
            elif action == "get_error_events":
                return self._get_error_events(params)
            elif action == "get_performance_stats":
                return self._get_performance_stats(params)
            elif action == "create_release":
                return self._create_release(params)
            elif action == "list_releases":
                return self._list_releases(params)
            elif action == "get_issue_tags":
                return self._get_issue_tags(params)
            elif action == "bulk_update_issues":
                return self._bulk_update_issues(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _list_issues(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List issues in the organization"""
        project_slug = params.get("project_slug", "")
        query = params.get("query", "")
        status = params.get("status", "")  # unresolved, resolved, ignored
        assigned_to = params.get("assigned_to", "")
        limit = params.get("limit", 25)

        endpoint = f"/organizations/{self.organization_slug}/issues/"
        query_params = {"limit": limit}

        if project_slug:
            query_params["project"] = project_slug
        if query:
            query_params["query"] = query
        if status:
            query_params["status"] = status
        if assigned_to:
            query_params["assignedTo"] = assigned_to

        result = self._make_request(endpoint, params=query_params)

        if "error" in result:
            return result

        return {
            "issues": result,
            "count": len(result) if isinstance(result, list) else 0
        }

    def _get_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific issue"""
        issue_id = params.get("issue_id", "")

        if not issue_id:
            return {"error": "issue_id parameter is required"}

        endpoint = f"/organizations/{self.organization_slug}/issues/{issue_id}/"
        result = self._make_request(endpoint)

        if "error" in result:
            return result

        return {"issue": result}

    def _update_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an issue"""
        issue_id = params.get("issue_id", "")
        data = params.get("data", {})

        if not issue_id:
            return {"error": "issue_id parameter is required"}

        if not data:
            return {"error": "data parameter is required"}

        endpoint = f"/organizations/{self.organization_slug}/issues/{issue_id}/"
        result = self._make_request(endpoint, "PUT", data)

        if "error" in result:
            return result

        return {"success": True, "issue": result}

    def _resolve_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve an issue"""
        issue_id = params.get("issue_id", "")

        if not issue_id:
            return {"error": "issue_id parameter is required"}

        endpoint = f"/organizations/{self.organization_slug}/issues/{issue_id}/"
        data = {"status": "resolved"}
        
        result = self._make_request(endpoint, "PUT", data)

        if "error" in result:
            return result

        return {"success": True, "message": "Issue resolved successfully"}

    def _create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a manual issue"""
        project_slug = params.get("project_slug", "")
        title = params.get("title", "")
        message = params.get("message", "")
        level = params.get("level", "error")  # fatal, error, warning, info, debug
        culprit = params.get("culprit", "")
        platform = params.get("platform", "other")

        if not project_slug or not title:
            return {"error": "project_slug and title parameters are required"}

        endpoint = f"/projects/{self.organization_slug}/{project_slug}/events/"
        
        data = {
            "message": message or title,
            "title": title,
            "level": level,
            "culprit": culprit,
            "platform": platform,
            "event_id": f"manual-{datetime.now().isoformat()}",
            "timestamp": datetime.now().isoformat(),
            "tags": {"manual": "true"}
        }

        result = self._make_request(endpoint, "POST", data)

        if "error" in result:
            return result

        return {"success": True, "event_id": result.get("id")}

    def _list_projects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List projects in the organization"""
        endpoint = f"/organizations/{self.organization_slug}/projects/"
        result = self._make_request(endpoint)

        if "error" in result:
            return result

        return {
            "projects": result,
            "count": len(result) if isinstance(result, list) else 0
        }

    def _get_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific project"""
        project_slug = params.get("project_slug", "")

        if not project_slug:
            return {"error": "project_slug parameter is required"}

        endpoint = f"/projects/{self.organization_slug}/{project_slug}/"
        result = self._make_request(endpoint)

        if "error" in result:
            return result

        return {"project": result}

    def _get_error_events(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get error events for an issue"""
        issue_id = params.get("issue_id", "")
        limit = params.get("limit", 10)

        if not issue_id:
            return {"error": "issue_id parameter is required"}

        endpoint = f"/organizations/{self.organization_slug}/issues/{issue_id}/events/"
        query_params = {"limit": limit}
        
        result = self._make_request(endpoint, params=query_params)

        if "error" in result:
            return result

        return {
            "events": result,
            "count": len(result) if isinstance(result, list) else 0
        }

    def _get_performance_stats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get performance statistics for a project"""
        project_slug = params.get("project_slug", "")
        stats_period = params.get("stats_period", "24h")  # 1h, 24h, 7d, 30d

        if not project_slug:
            return {"error": "project_slug parameter is required"}

        endpoint = f"/projects/{self.organization_slug}/{project_slug}/stats/"
        query_params = {"statPeriod": stats_period}
        
        result = self._make_request(endpoint, params=query_params)

        if "error" in result:
            return result

        return {"stats": result}

    def _create_release(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new release"""
        project_slug = params.get("project_slug", "")
        version = params.get("version", "")
        ref = params.get("ref", "")
        url = params.get("url", "")
        commits = params.get("commits", [])

        if not project_slug or not version:
            return {"error": "project_slug and version parameters are required"}

        endpoint = f"/projects/{self.organization_slug}/{project_slug}/releases/"
        
        data = {
            "version": version,
            "ref": ref,
            "url": url,
            "commits": commits
        }

        result = self._make_request(endpoint, "POST", data)

        if "error" in result:
            return result

        return {"success": True, "release": result}

    def _list_releases(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List releases for a project"""
        project_slug = params.get("project_slug", "")
        limit = params.get("limit", 25)

        if not project_slug:
            return {"error": "project_slug parameter is required"}

        endpoint = f"/projects/{self.organization_slug}/{project_slug}/releases/"
        query_params = {"limit": limit}
        
        result = self._make_request(endpoint, params=query_params)

        if "error" in result:
            return result

        return {
            "releases": result,
            "count": len(result) if isinstance(result, list) else 0
        }

    def _get_issue_tags(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get tags for an issue"""
        issue_id = params.get("issue_id", "")

        if not issue_id:
            return {"error": "issue_id parameter is required"}

        endpoint = f"/organizations/{self.organization_slug}/issues/{issue_id}/tags/"
        result = self._make_request(endpoint)

        if "error" in result:
            return result

        return {
            "tags": result,
            "count": len(result) if isinstance(result, list) else 0
        }

    def _bulk_update_issues(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk update multiple issues"""
        issue_ids = params.get("issue_ids", [])
        data = params.get("data", {})

        if not issue_ids:
            return {"error": "issue_ids parameter is required"}

        if not data:
            return {"error": "data parameter is required"}

        endpoint = f"/organizations/{self.organization_slug}/issues/bulk-update/"
        
        payload = {
            "data": data,
            "issues": issue_ids
        }

        result = self._make_request(endpoint, "PUT", payload)

        if "error" in result:
            return result

        return {"success": True, "updated": result}

    def cleanup(self):
        """Cleanup resources"""
        self.auth_token = None
        self.base_url = None
        self.organization_slug = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = SentryPlugin
PLUGIN_NAME = "sentry"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Sentry API for error monitoring and issue tracking"
PLUGIN_ACTIONS = [
    "list_issues", "get_issue", "update_issue", "resolve_issue", "create_issue",
    "list_projects", "get_project", "get_error_events", "get_performance_stats",
    "create_release", "list_releases", "get_issue_tags", "bulk_update_issues"
]