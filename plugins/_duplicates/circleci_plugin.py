"""
CircleCI DevOps Plugin
Supports CircleCI CI/CD operations via API
"""

from typing import Dict, Any, Optional, List
import os
import requests


class CircleCIPlugin:
    """Plugin for CircleCI CI/CD operations"""
    
    name = "circleci"
    version = "1.0.0"
    description = "Integration with CircleCI for CI/CD operations"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://circleci.com/api/v2"
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the CircleCI plugin"""
        try:
            # Get API key from config or environment
            self.api_key = (
                config.get("api_key") if config 
                else os.getenv("CIRCLECI_API_KEY")
            )
            
            if not self.api_key:
                return False
                
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Error initializing CircleCI plugin: {e}")
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a CircleCI action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide API key."}
        
        try:
            if action == "trigger_pipeline":
                return self._trigger_pipeline(params)
            elif action == "get_pipeline_status":
                return self._get_pipeline_status(params)
            elif action == "list_pipelines":
                return self._list_pipelines(params)
            elif action == "get_workflow_status":
                return self._get_workflow_status(params)
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _trigger_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a new pipeline"""
        project_slug = params.get("project_slug")
        branch = params.get("branch", "main")
        parameters = params.get("parameters", {})
        
        if not project_slug:
            return {"error": "project_slug is required"}
        
        url = f"{self.base_url}/project/{project_slug}/pipeline"
        headers = {
            "Circle-Token": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "branch": branch,
            "parameters": parameters
        }
        
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 201:
            return response.json()
        else:
            return {"error": f"Failed to trigger pipeline: {response.text}"}
    
    def _get_pipeline_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get pipeline status"""
        pipeline_id = params.get("pipeline_id")
        
        if not pipeline_id:
            return {"error": "pipeline_id is required"}
        
        url = f"{self.base_url}/pipeline/{pipeline_id}"
        headers = {"Circle-Token": self.api_key}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to get pipeline status: {response.text}"}
    
    def _list_pipelines(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List pipelines for a project"""
        project_slug = params.get("project_slug")
        page_token = params.get("page_token")
        
        if not project_slug:
            return {"error": "project_slug is required"}
        
        url = f"{self.base_url}/project/{project_slug}/pipeline"
        headers = {"Circle-Token": self.api_key}
        params_query = {}
        if page_token:
            params_query["page-token"] = page_token
        
        response = requests.get(url, headers=headers, params=params_query)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to list pipelines: {response.text}"}
    
    def _get_workflow_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get workflow status"""
        workflow_id = params.get("workflow_id")
        
        if not workflow_id:
            return {"error": "workflow_id is required"}
        
        url = f"{self.base_url}/workflow/{workflow_id}"
        headers = {"Circle-Token": self.api_key}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"Failed to get workflow status: {response.text}"}
    
    def cleanup(self):
        """Cleanup resources"""
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = CircleCIPlugin
PLUGIN_NAME = "circleci"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with CircleCI for CI/CD operations"
PLUGIN_ACTIONS = ["trigger_pipeline", "get_pipeline_status", "list_pipelines", "get_workflow_status"]