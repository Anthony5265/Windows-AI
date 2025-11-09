"""
GitLab Plugin
Supports GitLab CI/CD pipeline management through GitLab API
"""

from typing import Dict, Any, Optional, List
import os
import requests


class GitLabPlugin:
    """Plugin for GitLab CI/CD pipeline management"""

    name = "gitlab"
    version = "1.0.0"
    description = "Integration with GitLab API for CI/CD pipeline management"
    author = "Windows AI Team"

    def __init__(self):
        self.gitlab_token: Optional[str] = None
        self.base_url = "https://gitlab.com/api/v4"
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the GitLab plugin"""
        try:
            # Get GitLab token from config or environment
            self.gitlab_token = (
                config.get("gitlab_token") if config
                else os.getenv("GITLAB_TOKEN")
            )

            # Allow custom GitLab instance URL
            if config and config.get("base_url"):
                self.base_url = config["base_url"]

            if not self.gitlab_token:
                return False

            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing GitLab plugin: {e}")
            return False

    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to GitLab API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.gitlab_token}",
                "Content-Type": "application/json"
            }

            url = f"{self.base_url}{endpoint}"

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
        """Execute a GitLab action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide GitLab token."}

        try:
            if action == "list_projects":
                return self._list_projects(params)
            elif action == "get_project":
                return self._get_project(params)
            elif action == "list_pipelines":
                return self._list_pipelines(params)
            elif action == "get_pipeline":
                return self._get_pipeline(params)
            elif action == "trigger_pipeline":
                return self._trigger_pipeline(params)
            elif action == "cancel_pipeline":
                return self._cancel_pipeline(params)
            elif action == "retry_pipeline":
                return self._retry_pipeline(params)
            elif action == "get_pipeline_jobs":
                return self._get_pipeline_jobs(params)
            elif action == "get_job_log":
                return self._get_job_log(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _list_projects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List projects"""
        owned = params.get("owned", False)
        membership = params.get("membership", False)
        search = params.get("search", "")
        per_page = params.get("per_page", 20)

        query_params = {"per_page": per_page}
        if owned:
            query_params["owned"] = "true"
        if membership:
            query_params["membership"] = "true"
        if search:
            query_params["search"] = search

        endpoint = "/projects"
        result = self._make_request(endpoint, params=query_params)

        if "error" in result:
            return result

        return {"projects": result}

    def _get_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific project"""
        project_id = params.get("project_id", "")

        if not project_id:
            return {"error": "project_id parameter is required"}

        endpoint = f"/projects/{project_id}"
        result = self._make_request(endpoint)

        if "error" in result:
            return result

        return {"project": result}

    def _list_pipelines(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List pipelines for a project"""
        project_id = params.get("project_id", "")
        status = params.get("status", "")  # running, pending, success, failed, canceled, skipped
        ref = params.get("ref", "")
        per_page = params.get("per_page", 20)

        if not project_id:
            return {"error": "project_id parameter is required"}

        query_params = {"per_page": per_page}
        if status:
            query_params["status"] = status
        if ref:
            query_params["ref"] = ref

        endpoint = f"/projects/{project_id}/pipelines"
        result = self._make_request(endpoint, params=query_params)

        if "error" in result:
            return result

        return {"pipelines": result}

    def _get_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific pipeline"""
        project_id = params.get("project_id", "")
        pipeline_id = params.get("pipeline_id", "")

        if not project_id or not pipeline_id:
            return {"error": "project_id and pipeline_id parameters are required"}

        endpoint = f"/projects/{project_id}/pipelines/{pipeline_id}"
        result = self._make_request(endpoint)

        if "error" in result:
            return result

        return {"pipeline": result}

    def _trigger_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a pipeline"""
        project_id = params.get("project_id", "")
        ref = params.get("ref", "main")
        variables = params.get("variables", {})

        if not project_id:
            return {"error": "project_id parameter is required"}

        data = {"ref": ref}
        if variables:
            data["variables"] = [{"key": k, "value": v} for k, v in variables.items()]

        endpoint = f"/projects/{project_id}/pipeline"
        result = self._make_request(endpoint, "POST", data)

        if "error" in result:
            return result

        return {"pipeline": result}

    def _cancel_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cancel a pipeline"""
        project_id = params.get("project_id", "")
        pipeline_id = params.get("pipeline_id", "")

        if not project_id or not pipeline_id:
            return {"error": "project_id and pipeline_id parameters are required"}

        endpoint = f"/projects/{project_id}/pipelines/{pipeline_id}/cancel"
        result = self._make_request(endpoint, "POST")

        if "error" in result:
            return result

        return {"success": True, "message": "Pipeline cancelled successfully"}

    def _retry_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retry a pipeline"""
        project_id = params.get("project_id", "")
        pipeline_id = params.get("pipeline_id", "")

        if not project_id or not pipeline_id:
            return {"error": "project_id and pipeline_id parameters are required"}

        endpoint = f"/projects/{project_id}/pipelines/{pipeline_id}/retry"
        result = self._make_request(endpoint, "POST")

        if "error" in result:
            return result

        return {"pipeline": result}

    def _get_pipeline_jobs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get jobs for a pipeline"""
        project_id = params.get("project_id", "")
        pipeline_id = params.get("pipeline_id", "")

        if not project_id or not pipeline_id:
            return {"error": "project_id and pipeline_id parameters are required"}

        endpoint = f"/projects/{project_id}/pipelines/{pipeline_id}/jobs"
        result = self._make_request(endpoint)

        if "error" in result:
            return result

        return {"jobs": result}

    def _get_job_log(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get log for a specific job"""
        project_id = params.get("project_id", "")
        job_id = params.get("job_id", "")

        if not project_id or not job_id:
            return {"error": "project_id and job_id parameters are required"}

        endpoint = f"/projects/{project_id}/jobs/{job_id}/trace"
        result = self._make_request(endpoint)

        if "error" in result:
            return result

        return {"log": result}

    def cleanup(self):
        """Cleanup resources"""
        self.gitlab_token = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = GitLabPlugin
PLUGIN_NAME = "gitlab"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with GitLab API for CI/CD pipeline management"
PLUGIN_ACTIONS = ["list_projects", "get_project", "list_pipelines", "get_pipeline", "trigger_pipeline", "cancel_pipeline", "retry_pipeline", "get_pipeline_jobs", "get_job_log"]