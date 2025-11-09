"""
GitHub Integration Plugin
"""

from typing import Dict, Any, Optional, List
import os


class GitHubPlugin:
    """Plugin for GitHub integration"""
    
    name = "github"
    version = "1.0.0"
    description = "Integration with GitHub API"
    author = "Windows AI Team"
    
    def __init__(self):
        self.api_key: Optional[str] = None
        self.client = None
        self._initialized = False
        
    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        try:
            import requests
            self.api_key = config.get("api_key") if config else os.getenv("GITHUB_TOKEN")
            if not self.api_key:
                return False
            self.client = requests
            self._initialized = True
            return True
        except ImportError:
            return False
        except Exception:
            return False
    
    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}
        try:
            if action == "create_repo":
                return self._create_repo(params)
            elif action == "list_repos":
                return self._list_repos(params)
            elif action == "create_issue":
                return self._create_issue(params)
            elif action == "get_pr":
                return self._get_pr(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _create_repo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name", "")
        private = params.get("private", False)
        headers = {"Authorization": f"token {self.api_key}"}
        response = self.client.post("https://api.github.com/user/repos", headers=headers, json={"name": name, "private": private})
        return {"success": response.status_code == 201, "data": response.json() if response.status_code == 201 else None}
    
    def _list_repos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Authorization": f"token {self.api_key}"}
        response = self.client.get("https://api.github.com/user/repos", headers=headers)
        return {"success": response.status_code == 200, "repos": response.json() if response.status_code == 200 else []}
    
    def _create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        repo = params.get("repo", "")
        title = params.get("title", "")
        body = params.get("body", "")
        headers = {"Authorization": f"token {self.api_key}"}
        response = self.client.post(f"https://api.github.com/repos/{repo}/issues", headers=headers, json={"title": title, "body": body})
        return {"success": response.status_code == 201, "issue": response.json() if response.status_code == 201 else None}
    
    def _get_pr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        repo = params.get("repo", "")
        pr_number = params.get("pr_number", 0)
        headers = {"Authorization": f"token {self.api_key}"}
        response = self.client.get(f"https://api.github.com/repos/{repo}/pulls/{pr_number}", headers=headers)
        return {"success": response.status_code == 200, "pr": response.json() if response.status_code == 200 else None}
    
    def shutdown(self) -> bool:
        self._initialized = False
        return True
