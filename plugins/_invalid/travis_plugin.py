"""
Travis CI Plugin
Integration with Travis CI for continuous integration and deployment
"""

from typing import Dict, Any, Optional, List
import os
import requests
import logging
from datetime import datetime


class TravisPlugin:
    """Plugin for Travis CI integration"""

    name = "travis"
    version = "1.0.0"
    description = "Integration with Travis CI for continuous integration and deployment"
    author = "Windows AI Team"

    def __init__(self):
        self.api_token: Optional[str] = None
        self.base_url = "https://api.travis-ci.com"
        self._initialized = False
        self.logger = logging.getLogger(__name__)

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Travis CI plugin"""
        try:
            # Get API token from config or environment
            self.api_token = (
                config.get("api_token") if config
                else os.getenv("TRAVIS_API_TOKEN")
            )

            if not self.api_token:
                self.logger.error("No Travis CI API token provided")
                return False

            # Set headers for API requests
            self.headers = {
                "Authorization": f"token {self.api_token}",
                "Travis-API-Version": "3",
                "Accept": "application/json"
            }

            self._initialized = True
            self.logger.info("Travis CI plugin initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing Travis CI plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Travis CI action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide Travis CI API token."}

        try:
            if action == "trigger_build":
                return self._trigger_build(params)
            elif action == "get_build_status":
                return self._get_build_status(params)
            elif action == "list_builds":
                return self._list_builds(params)
            elif action == "get_repo_info":
                return self._get_repo_info(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {"error": str(e)}

    def _trigger_build(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger a new build for a repository"""
        repo_slug = params.get("repo_slug", "")
        branch = params.get("branch", "main")
        message = params.get("message", "Triggered by Windows AI")

        if not repo_slug:
            return {"error": "Repository slug is required"}

        url = f"{self.base_url}/repo/{repo_slug}/requests"

        payload = {
            "request": {
                "branch": branch,
                "message": message
            }
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            data = response.json()
            return {
                "success": True,
                "build_id": data.get("request", {}).get("id"),
                "repo_slug": repo_slug,
                "branch": branch,
                "message": message
            }

        except requests.RequestException as e:
            self.logger.error(f"Error triggering build: {e}")
            return {"error": f"Failed to trigger build: {e}"}

    def _get_build_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the status of a specific build"""
        build_id = params.get("build_id", "")
        repo_slug = params.get("repo_slug", "")

        if not build_id and not repo_slug:
            return {"error": "Either build_id or repo_slug is required"}

        try:
            if build_id:
                url = f"{self.base_url}/build/{build_id}"
            else:
                # Get latest build for repo
                url = f"{self.base_url}/repo/{repo_slug}/builds?limit=1"

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            build = data if build_id else data.get("builds", [{}])[0]

            return {
                "success": True,
                "build_id": build.get("id"),
                "state": build.get("state"),
                "number": build.get("number"),
                "commit": build.get("commit", {}).get("sha"),
                "branch": build.get("branch", {}).get("name"),
                "started_at": build.get("started_at"),
                "finished_at": build.get("finished_at"),
                "duration": build.get("duration")
            }

        except requests.RequestException as e:
            self.logger.error(f"Error getting build status: {e}")
            return {"error": f"Failed to get build status: {e}"}

    def _list_builds(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List builds for a repository"""
        repo_slug = params.get("repo_slug", "")
        limit = params.get("limit", 10)

        if not repo_slug:
            return {"error": "Repository slug is required"}

        url = f"{self.base_url}/repo/{repo_slug}/builds?limit={limit}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            builds = data.get("builds", [])

            build_list = []
            for build in builds:
                build_list.append({
                    "id": build.get("id"),
                    "number": build.get("number"),
                    "state": build.get("state"),
                    "branch": build.get("branch", {}).get("name"),
                    "commit": build.get("commit", {}).get("sha"),
                    "started_at": build.get("started_at"),
                    "finished_at": build.get("finished_at")
                })

            return {
                "success": True,
                "repo_slug": repo_slug,
                "builds": build_list,
                "count": len(build_list)
            }

        except requests.RequestException as e:
            self.logger.error(f"Error listing builds: {e}")
            return {"error": f"Failed to list builds: {e}"}

    def _get_repo_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a repository"""
        repo_slug = params.get("repo_slug", "")

        if not repo_slug:
            return {"error": "Repository slug is required"}

        url = f"{self.base_url}/repo/{repo_slug}"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()

            return {
                "success": True,
                "repo_slug": repo_slug,
                "name": data.get("name"),
                "description": data.get("description"),
                "active": data.get("active"),
                "private": data.get("private"),
                "default_branch": data.get("default_branch", {}).get("name"),
                "language": data.get("language"),
                "last_build": data.get("last_build", {}).get("id")
            }

        except requests.RequestException as e:
            self.logger.error(f"Error getting repo info: {e}")
            return {"error": f"Failed to get repo info: {e}"}

    def cleanup(self):
        """Cleanup resources"""
        self.api_token = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = TravisPlugin
PLUGIN_NAME = "travis"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Travis CI for continuous integration and deployment"
PLUGIN_ACTIONS = ["trigger_build", "get_build_status", "list_builds", "get_repo_info"]