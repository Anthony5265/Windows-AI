"""
GitHub Integration Plugin

Integrates Windows AI with GitHub for repository management, issues, PRs, and more.
"""

from typing import Dict, Any, Optional
import httpx
import logging
import os

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class GitHubPlugin(IntegrationPlugin):
    """
    GitHub integration for Windows AI.
    Allows creating issues, listing repos, managing PRs, etc.
    """

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            id="github",
            name="GitHub Integration",
            description="Interact with GitHub repositories, issues, and pull requests",
            version="1.0.0",
            author="Windows AI",
            plugin_type=PluginType.INTEGRATION,
            icon="🐙",
            tags=["github", "git", "version-control", "collaboration"],
            requirements=["httpx"]
        )

    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.client: Optional[httpx.AsyncClient] = None
        self.token: Optional[str] = None
        self.base_url = "https://api.github.com"

    async def initialize(self) -> bool:
        """Initialize the GitHub plugin"""
        # Try to get token from environment
        self.token = os.getenv("GITHUB_TOKEN")
        if self.token:
            logger.info("GitHub token found in environment")
        else:
            logger.warning("No GitHub token found. Some operations will be limited.")

        self._initialized = True
        return True

    async def connect(self, credentials: Dict[str, str]) -> bool:
        """
        Connect to GitHub with credentials.

        Args:
            credentials: Dict with 'token' key

        Returns:
            True if connected successfully
        """
        try:
            self.token = credentials.get("token")
            if not self.token:
                logger.error("No GitHub token provided")
                return False

            # Create HTTP client
            headers = {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            self.client = httpx.AsyncClient(headers=headers, timeout=30.0)

            # Test the connection
            response = await self.client.get(f"{self.base_url}/user")
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Connected to GitHub as: {user_data.get('login')}")
                return True
            else:
                logger.error(f"GitHub connection failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error connecting to GitHub: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from GitHub"""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.token = None
        return True

    async def execute(
        self,
        action: str,
        parameters: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a GitHub action.

        Actions:
        - list_repos: List user's repositories
        - get_repo: Get repository details
        - create_issue: Create an issue
        - list_issues: List issues in a repository
        - create_pr: Create a pull request
        - list_prs: List pull requests
        - get_user: Get user information
        - search_repos: Search repositories

        Args:
            action: The action to perform
            parameters: Action parameters
        """
        # Ensure we have a client
        if not self.client and self.token:
            await self.connect({"token": self.token})

        if not self.client:
            return {
                "success": False,
                "error": "Not connected to GitHub. Please provide a token."
            }

        try:
            if action == "list_repos":
                return await self._list_repos(parameters)
            elif action == "get_repo":
                return await self._get_repo(parameters)
            elif action == "create_issue":
                return await self._create_issue(parameters)
            elif action == "list_issues":
                return await self._list_issues(parameters)
            elif action == "create_pr":
                return await self._create_pr(parameters)
            elif action == "list_prs":
                return await self._list_prs(parameters)
            elif action == "get_user":
                return await self._get_user(parameters)
            elif action == "search_repos":
                return await self._search_repos(parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }

        except Exception as e:
            logger.error(f"Error executing GitHub action {action}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _list_repos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List user's repositories"""
        username = params.get("username", "")
        per_page = params.get("per_page", 30)

        url = f"{self.base_url}/user/repos" if not username else f"{self.base_url}/users/{username}/repos"
        response = await self.client.get(url, params={"per_page": per_page, "sort": "updated"})

        if response.status_code == 200:
            repos = response.json()
            return {
                "success": True,
                "result": [
                    {
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo.get("description"),
                        "url": repo["html_url"],
                        "stars": repo["stargazers_count"],
                        "language": repo.get("language"),
                        "updated_at": repo["updated_at"]
                    }
                    for repo in repos
                ],
                "message": f"Found {len(repos)} repositories"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to list repos: {response.status_code}"
            }

    async def _get_repo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository details"""
        owner = params.get("owner")
        repo = params.get("repo")

        if not owner or not repo:
            return {"success": False, "error": "owner and repo are required"}

        response = await self.client.get(f"{self.base_url}/repos/{owner}/{repo}")

        if response.status_code == 200:
            repo_data = response.json()
            return {
                "success": True,
                "result": {
                    "name": repo_data["name"],
                    "full_name": repo_data["full_name"],
                    "description": repo_data.get("description"),
                    "url": repo_data["html_url"],
                    "stars": repo_data["stargazers_count"],
                    "forks": repo_data["forks_count"],
                    "open_issues": repo_data["open_issues_count"],
                    "language": repo_data.get("language"),
                    "created_at": repo_data["created_at"],
                    "updated_at": repo_data["updated_at"]
                }
            }
        else:
            return {
                "success": False,
                "error": f"Failed to get repo: {response.status_code}"
            }

    async def _create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an issue"""
        owner = params.get("owner")
        repo = params.get("repo")
        title = params.get("title")
        body = params.get("body", "")
        labels = params.get("labels", [])

        if not owner or not repo or not title:
            return {"success": False, "error": "owner, repo, and title are required"}

        data = {
            "title": title,
            "body": body,
            "labels": labels
        }

        response = await self.client.post(
            f"{self.base_url}/repos/{owner}/{repo}/issues",
            json=data
        )

        if response.status_code == 201:
            issue = response.json()
            return {
                "success": True,
                "result": {
                    "number": issue["number"],
                    "title": issue["title"],
                    "url": issue["html_url"],
                    "state": issue["state"]
                },
                "message": f"Created issue #{issue['number']}"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to create issue: {response.status_code}"
            }

    async def _list_issues(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List issues in a repository"""
        owner = params.get("owner")
        repo = params.get("repo")
        state = params.get("state", "open")
        per_page = params.get("per_page", 30)

        if not owner or not repo:
            return {"success": False, "error": "owner and repo are required"}

        response = await self.client.get(
            f"{self.base_url}/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": per_page}
        )

        if response.status_code == 200:
            issues = response.json()
            return {
                "success": True,
                "result": [
                    {
                        "number": issue["number"],
                        "title": issue["title"],
                        "state": issue["state"],
                        "url": issue["html_url"],
                        "created_at": issue["created_at"],
                        "updated_at": issue["updated_at"],
                        "labels": [label["name"] for label in issue.get("labels", [])]
                    }
                    for issue in issues if "pull_request" not in issue  # Filter out PRs
                ],
                "message": f"Found {len(issues)} issues"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to list issues: {response.status_code}"
            }

    async def _create_pr(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a pull request"""
        owner = params.get("owner")
        repo = params.get("repo")
        title = params.get("title")
        head = params.get("head")  # Branch to merge from
        base = params.get("base", "main")  # Branch to merge into
        body = params.get("body", "")

        if not owner or not repo or not title or not head:
            return {"success": False, "error": "owner, repo, title, and head are required"}

        data = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }

        response = await self.client.post(
            f"{self.base_url}/repos/{owner}/{repo}/pulls",
            json=data
        )

        if response.status_code == 201:
            pr = response.json()
            return {
                "success": True,
                "result": {
                    "number": pr["number"],
                    "title": pr["title"],
                    "url": pr["html_url"],
                    "state": pr["state"]
                },
                "message": f"Created PR #{pr['number']}"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to create PR: {response.status_code}"
            }

    async def _list_prs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List pull requests"""
        owner = params.get("owner")
        repo = params.get("repo")
        state = params.get("state", "open")
        per_page = params.get("per_page", 30)

        if not owner or not repo:
            return {"success": False, "error": "owner and repo are required"}

        response = await self.client.get(
            f"{self.base_url}/repos/{owner}/{repo}/pulls",
            params={"state": state, "per_page": per_page}
        )

        if response.status_code == 200:
            prs = response.json()
            return {
                "success": True,
                "result": [
                    {
                        "number": pr["number"],
                        "title": pr["title"],
                        "state": pr["state"],
                        "url": pr["html_url"],
                        "head": pr["head"]["ref"],
                        "base": pr["base"]["ref"],
                        "created_at": pr["created_at"],
                        "updated_at": pr["updated_at"]
                    }
                    for pr in prs
                ],
                "message": f"Found {len(prs)} pull requests"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to list PRs: {response.status_code}"
            }

    async def _get_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get user information"""
        username = params.get("username", "")

        url = f"{self.base_url}/user" if not username else f"{self.base_url}/users/{username}"
        response = await self.client.get(url)

        if response.status_code == 200:
            user = response.json()
            return {
                "success": True,
                "result": {
                    "login": user["login"],
                    "name": user.get("name"),
                    "bio": user.get("bio"),
                    "location": user.get("location"),
                    "email": user.get("email"),
                    "public_repos": user["public_repos"],
                    "followers": user["followers"],
                    "following": user["following"],
                    "url": user["html_url"]
                }
            }
        else:
            return {
                "success": False,
                "error": f"Failed to get user: {response.status_code}"
            }

    async def _search_repos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search repositories"""
        query = params.get("query")
        per_page = params.get("per_page", 10)

        if not query:
            return {"success": False, "error": "query is required"}

        response = await self.client.get(
            f"{self.base_url}/search/repositories",
            params={"q": query, "per_page": per_page, "sort": "stars"}
        )

        if response.status_code == 200:
            data = response.json()
            repos = data.get("items", [])
            return {
                "success": True,
                "result": [
                    {
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "description": repo.get("description"),
                        "url": repo["html_url"],
                        "stars": repo["stargazers_count"],
                        "language": repo.get("language")
                    }
                    for repo in repos
                ],
                "message": f"Found {len(repos)} repositories"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to search repos: {response.status_code}"
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return parameter schema"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "list_repos", "get_repo", "create_issue", "list_issues",
                        "create_pr", "list_prs", "get_user", "search_repos"
                    ],
                    "description": "The GitHub action to perform"
                },
                "parameters": {
                    "type": "object",
                    "description": "Action-specific parameters"
                }
            },
            "required": ["action", "parameters"]
        }
