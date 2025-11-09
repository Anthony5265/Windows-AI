"""
GitHub Enhanced Plugin
Full-featured GitHub integration with official PyGithub SDK
"""
from typing import Dict, Any, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

try:
    from github import Github, GithubException
    from github.Repository import Repository
    from github.Issue import Issue
    from github.PullRequest import PullRequest
    GITHUB_SDK_AVAILABLE = True
except ImportError:
    GITHUB_SDK_AVAILABLE = False
    logger.warning("PyGithub not installed. Install with: pip install PyGithub")


class Plugin:
    """Enhanced GitHub plugin with full SDK integration"""

    def __init__(self):
        self.name = "GitHub Enhanced"
        self.version = "2.0.0"
        self.description = "Full GitHub integration: repos, issues, PRs, actions, releases"

        # Configuration
        self.token = os.getenv("GITHUB_TOKEN", os.getenv("GH_TOKEN", ""))
        self.client: Optional[Github] = None

        # Initialize client
        if GITHUB_SDK_AVAILABLE and self.token:
            try:
                self.client = Github(self.token)
                logger.info("GitHub client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize GitHub client: {e}")

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute GitHub operation

        Args:
            action (str): Action to perform
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not GITHUB_SDK_AVAILABLE:
            return {
                "status": "error",
                "message": "PyGithub not installed. Install with: pip install PyGithub"
            }

        if not self.token or not self.client:
            return {
                "status": "error",
                "message": "GitHub token not configured. Set GITHUB_TOKEN environment variable."
            }

        try:
            action = kwargs.get("action", "list_repos")

            # Route to appropriate handler
            if action == "list_repos":
                return await self._list_repos(**kwargs)
            elif action == "get_repo":
                return await self._get_repo(**kwargs)
            elif action == "create_repo":
                return await self._create_repo(**kwargs)
            elif action == "list_issues":
                return await self._list_issues(**kwargs)
            elif action == "get_issue":
                return await self._get_issue(**kwargs)
            elif action == "create_issue":
                return await self._create_issue(**kwargs)
            elif action == "update_issue":
                return await self._update_issue(**kwargs)
            elif action == "close_issue":
                return await self._close_issue(**kwargs)
            elif action == "comment_issue":
                return await self._comment_issue(**kwargs)
            elif action == "list_prs":
                return await self._list_prs(**kwargs)
            elif action == "get_pr":
                return await self._get_pr(**kwargs)
            elif action == "create_pr":
                return await self._create_pr(**kwargs)
            elif action == "merge_pr":
                return await self._merge_pr(**kwargs)
            elif action == "list_releases":
                return await self._list_releases(**kwargs)
            elif action == "create_release":
                return await self._create_release(**kwargs)
            elif action == "get_contents":
                return await self._get_contents(**kwargs)
            elif action == "create_file":
                return await self._create_file(**kwargs)
            elif action == "update_file":
                return await self._update_file(**kwargs)
            elif action == "search_code":
                return await self._search_code(**kwargs)
            elif action == "search_repos":
                return await self._search_repos(**kwargs)
            elif action == "get_user":
                return await self._get_user(**kwargs)
            elif action == "list_commits":
                return await self._list_commits(**kwargs)
            elif action == "get_actions_runs":
                return await self._get_actions_runs(**kwargs)
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except GithubException as e:
            logger.error(f"GitHub API error: {e.data.get('message', str(e))}")
            return {
                "status": "error",
                "message": e.data.get('message', str(e)),
                "status_code": e.status
            }
        except Exception as e:
            logger.error(f"GitHub error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _list_repos(self, **kwargs) -> Dict[str, Any]:
        """List repositories"""
        user = kwargs.get("user", None)
        org = kwargs.get("org", None)
        affiliation = kwargs.get("affiliation", "owner")  # owner, collaborator, organization_member
        max_repos = kwargs.get("max_repos", 30)

        repos = []
        if user:
            user_obj = self.client.get_user(user)
            repo_list = user_obj.get_repos()
        elif org:
            org_obj = self.client.get_organization(org)
            repo_list = org_obj.get_repos()
        else:
            repo_list = self.client.get_user().get_repos(affiliation=affiliation)

        for i, repo in enumerate(repo_list):
            if i >= max_repos:
                break
            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "url": repo.html_url,
                "language": repo.language
            })

        return {
            "status": "success",
            "repos": repos,
            "count": len(repos)
        }

    async def _get_repo(self, **kwargs) -> Dict[str, Any]:
        """Get repository details"""
        repo_name = kwargs.get("repo", kwargs.get("repository", ""))

        repo = self.client.get_repo(repo_name)

        return {
            "status": "success",
            "repo": {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "open_issues": repo.open_issues_count,
                "url": repo.html_url,
                "language": repo.language,
                "created_at": repo.created_at.isoformat(),
                "updated_at": repo.updated_at.isoformat()
            }
        }

    async def _create_repo(self, **kwargs) -> Dict[str, Any]:
        """Create a new repository"""
        name = kwargs.get("name", "")
        description = kwargs.get("description", "")
        private = kwargs.get("private", False)
        auto_init = kwargs.get("auto_init", False)

        user = self.client.get_user()
        repo = user.create_repo(
            name=name,
            description=description,
            private=private,
            auto_init=auto_init
        )

        return {
            "status": "success",
            "repo": {
                "name": repo.name,
                "full_name": repo.full_name,
                "url": repo.html_url
            }
        }

    async def _list_issues(self, **kwargs) -> Dict[str, Any]:
        """List issues in a repository"""
        repo_name = kwargs.get("repo", "")
        state = kwargs.get("state", "open")  # open, closed, all
        labels = kwargs.get("labels", [])
        max_issues = kwargs.get("max_issues", 30)

        repo = self.client.get_repo(repo_name)
        issue_list = repo.get_issues(state=state, labels=labels)

        issues = []
        for i, issue in enumerate(issue_list):
            if i >= max_issues:
                break
            if not issue.pull_request:  # Exclude PRs
                issues.append({
                    "number": issue.number,
                    "title": issue.title,
                    "state": issue.state,
                    "user": issue.user.login,
                    "labels": [label.name for label in issue.labels],
                    "comments": issue.comments,
                    "created_at": issue.created_at.isoformat(),
                    "url": issue.html_url
                })

        return {
            "status": "success",
            "issues": issues,
            "count": len(issues)
        }

    async def _get_issue(self, **kwargs) -> Dict[str, Any]:
        """Get issue details"""
        repo_name = kwargs.get("repo", "")
        issue_number = kwargs.get("issue_number", kwargs.get("number", 0))

        repo = self.client.get_repo(repo_name)
        issue = repo.get_issue(issue_number)

        return {
            "status": "success",
            "issue": {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "user": issue.user.login,
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees],
                "comments": issue.comments,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "url": issue.html_url
            }
        }

    async def _create_issue(self, **kwargs) -> Dict[str, Any]:
        """Create a new issue"""
        repo_name = kwargs.get("repo", "")
        title = kwargs.get("title", "")
        body = kwargs.get("body", "")
        labels = kwargs.get("labels", [])
        assignees = kwargs.get("assignees", [])

        repo = self.client.get_repo(repo_name)
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=labels,
            assignees=assignees
        )

        return {
            "status": "success",
            "issue": {
                "number": issue.number,
                "title": issue.title,
                "url": issue.html_url
            }
        }

    async def _update_issue(self, **kwargs) -> Dict[str, Any]:
        """Update an issue"""
        repo_name = kwargs.get("repo", "")
        issue_number = kwargs.get("issue_number", kwargs.get("number", 0))
        title = kwargs.get("title", None)
        body = kwargs.get("body", None)
        state = kwargs.get("state", None)
        labels = kwargs.get("labels", None)

        repo = self.client.get_repo(repo_name)
        issue = repo.get_issue(issue_number)

        if title:
            issue.edit(title=title)
        if body:
            issue.edit(body=body)
        if state:
            issue.edit(state=state)
        if labels is not None:
            issue.edit(labels=labels)

        return {
            "status": "success",
            "issue": {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state
            }
        }

    async def _close_issue(self, **kwargs) -> Dict[str, Any]:
        """Close an issue"""
        repo_name = kwargs.get("repo", "")
        issue_number = kwargs.get("issue_number", kwargs.get("number", 0))

        repo = self.client.get_repo(repo_name)
        issue = repo.get_issue(issue_number)
        issue.edit(state="closed")

        return {
            "status": "success",
            "issue": {
                "number": issue.number,
                "state": "closed"
            }
        }

    async def _comment_issue(self, **kwargs) -> Dict[str, Any]:
        """Comment on an issue"""
        repo_name = kwargs.get("repo", "")
        issue_number = kwargs.get("issue_number", kwargs.get("number", 0))
        comment = kwargs.get("comment", kwargs.get("body", ""))

        repo = self.client.get_repo(repo_name)
        issue = repo.get_issue(issue_number)
        comment_obj = issue.create_comment(comment)

        return {
            "status": "success",
            "comment": {
                "id": comment_obj.id,
                "url": comment_obj.html_url
            }
        }

    async def _list_prs(self, **kwargs) -> Dict[str, Any]:
        """List pull requests"""
        repo_name = kwargs.get("repo", "")
        state = kwargs.get("state", "open")
        max_prs = kwargs.get("max_prs", 30)

        repo = self.client.get_repo(repo_name)
        pr_list = repo.get_pulls(state=state)

        prs = []
        for i, pr in enumerate(pr_list):
            if i >= max_prs:
                break
            prs.append({
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "user": pr.user.login,
                "head": pr.head.ref,
                "base": pr.base.ref,
                "mergeable": pr.mergeable,
                "merged": pr.merged,
                "created_at": pr.created_at.isoformat(),
                "url": pr.html_url
            })

        return {
            "status": "success",
            "pull_requests": prs,
            "count": len(prs)
        }

    async def _get_pr(self, **kwargs) -> Dict[str, Any]:
        """Get pull request details"""
        repo_name = kwargs.get("repo", "")
        pr_number = kwargs.get("pr_number", kwargs.get("number", 0))

        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)

        return {
            "status": "success",
            "pull_request": {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "user": pr.user.login,
                "head": pr.head.ref,
                "base": pr.base.ref,
                "mergeable": pr.mergeable,
                "merged": pr.merged,
                "commits": pr.commits,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
                "created_at": pr.created_at.isoformat(),
                "url": pr.html_url
            }
        }

    async def _create_pr(self, **kwargs) -> Dict[str, Any]:
        """Create a pull request"""
        repo_name = kwargs.get("repo", "")
        title = kwargs.get("title", "")
        body = kwargs.get("body", "")
        head = kwargs.get("head", "")  # source branch
        base = kwargs.get("base", "main")  # target branch

        repo = self.client.get_repo(repo_name)
        pr = repo.create_pull(
            title=title,
            body=body,
            head=head,
            base=base
        )

        return {
            "status": "success",
            "pull_request": {
                "number": pr.number,
                "title": pr.title,
                "url": pr.html_url
            }
        }

    async def _merge_pr(self, **kwargs) -> Dict[str, Any]:
        """Merge a pull request"""
        repo_name = kwargs.get("repo", "")
        pr_number = kwargs.get("pr_number", kwargs.get("number", 0))
        commit_message = kwargs.get("commit_message", "")
        merge_method = kwargs.get("merge_method", "merge")  # merge, squash, rebase

        repo = self.client.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        result = pr.merge(
            commit_message=commit_message,
            merge_method=merge_method
        )

        return {
            "status": "success",
            "merged": result.merged,
            "message": result.message
        }

    async def _list_releases(self, **kwargs) -> Dict[str, Any]:
        """List releases"""
        repo_name = kwargs.get("repo", "")
        max_releases = kwargs.get("max_releases", 10)

        repo = self.client.get_repo(repo_name)
        release_list = repo.get_releases()

        releases = []
        for i, release in enumerate(release_list):
            if i >= max_releases:
                break
            releases.append({
                "tag_name": release.tag_name,
                "name": release.title,
                "body": release.body,
                "draft": release.draft,
                "prerelease": release.prerelease,
                "created_at": release.created_at.isoformat(),
                "published_at": release.published_at.isoformat() if release.published_at else None,
                "url": release.html_url
            })

        return {
            "status": "success",
            "releases": releases,
            "count": len(releases)
        }

    async def _create_release(self, **kwargs) -> Dict[str, Any]:
        """Create a release"""
        repo_name = kwargs.get("repo", "")
        tag_name = kwargs.get("tag_name", "")
        name = kwargs.get("name", "")
        body = kwargs.get("body", "")
        draft = kwargs.get("draft", False)
        prerelease = kwargs.get("prerelease", False)

        repo = self.client.get_repo(repo_name)
        release = repo.create_git_release(
            tag=tag_name,
            name=name,
            message=body,
            draft=draft,
            prerelease=prerelease
        )

        return {
            "status": "success",
            "release": {
                "tag_name": release.tag_name,
                "name": release.title,
                "url": release.html_url
            }
        }

    async def _get_contents(self, **kwargs) -> Dict[str, Any]:
        """Get file contents from repository"""
        repo_name = kwargs.get("repo", "")
        path = kwargs.get("path", "")
        ref = kwargs.get("ref", None)  # branch/tag/commit

        repo = self.client.get_repo(repo_name)
        contents = repo.get_contents(path, ref=ref)

        if isinstance(contents, list):
            # Directory
            files = []
            for item in contents:
                files.append({
                    "name": item.name,
                    "path": item.path,
                    "type": item.type,
                    "size": item.size
                })
            return {
                "status": "success",
                "type": "directory",
                "files": files
            }
        else:
            # File
            return {
                "status": "success",
                "type": "file",
                "file": {
                    "name": contents.name,
                    "path": contents.path,
                    "size": contents.size,
                    "content": contents.decoded_content.decode('utf-8'),
                    "sha": contents.sha
                }
            }

    async def _create_file(self, **kwargs) -> Dict[str, Any]:
        """Create a new file"""
        repo_name = kwargs.get("repo", "")
        path = kwargs.get("path", "")
        message = kwargs.get("message", "Create file")
        content = kwargs.get("content", "")
        branch = kwargs.get("branch", None)

        repo = self.client.get_repo(repo_name)
        result = repo.create_file(
            path=path,
            message=message,
            content=content,
            branch=branch
        )

        return {
            "status": "success",
            "file": {
                "path": result["content"].path,
                "sha": result["content"].sha,
                "url": result["content"].html_url
            }
        }

    async def _update_file(self, **kwargs) -> Dict[str, Any]:
        """Update an existing file"""
        repo_name = kwargs.get("repo", "")
        path = kwargs.get("path", "")
        message = kwargs.get("message", "Update file")
        content = kwargs.get("content", "")
        sha = kwargs.get("sha", "")
        branch = kwargs.get("branch", None)

        repo = self.client.get_repo(repo_name)
        result = repo.update_file(
            path=path,
            message=message,
            content=content,
            sha=sha,
            branch=branch
        )

        return {
            "status": "success",
            "file": {
                "path": result["content"].path,
                "sha": result["content"].sha
            }
        }

    async def _search_code(self, **kwargs) -> Dict[str, Any]:
        """Search code"""
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 30)

        results = self.client.search_code(query=query)

        code_results = []
        for i, result in enumerate(results):
            if i >= max_results:
                break
            code_results.append({
                "name": result.name,
                "path": result.path,
                "repository": result.repository.full_name,
                "url": result.html_url
            })

        return {
            "status": "success",
            "results": code_results,
            "count": len(code_results)
        }

    async def _search_repos(self, **kwargs) -> Dict[str, Any]:
        """Search repositories"""
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 30)

        results = self.client.search_repositories(query=query)

        repos = []
        for i, repo in enumerate(results):
            if i >= max_results:
                break
            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "stars": repo.stargazers_count,
                "language": repo.language,
                "url": repo.html_url
            })

        return {
            "status": "success",
            "repos": repos,
            "count": len(repos)
        }

    async def _get_user(self, **kwargs) -> Dict[str, Any]:
        """Get user information"""
        username = kwargs.get("username", None)

        if username:
            user = self.client.get_user(username)
        else:
            user = self.client.get_user()

        return {
            "status": "success",
            "user": {
                "login": user.login,
                "name": user.name,
                "email": user.email,
                "bio": user.bio,
                "company": user.company,
                "location": user.location,
                "public_repos": user.public_repos,
                "followers": user.followers,
                "following": user.following,
                "url": user.html_url
            }
        }

    async def _list_commits(self, **kwargs) -> Dict[str, Any]:
        """List commits"""
        repo_name = kwargs.get("repo", "")
        branch = kwargs.get("branch", None)
        max_commits = kwargs.get("max_commits", 30)

        repo = self.client.get_repo(repo_name)
        commits = repo.get_commits(sha=branch)

        commit_list = []
        for i, commit in enumerate(commits):
            if i >= max_commits:
                break
            commit_list.append({
                "sha": commit.sha,
                "message": commit.commit.message,
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.isoformat(),
                "url": commit.html_url
            })

        return {
            "status": "success",
            "commits": commit_list,
            "count": len(commit_list)
        }

    async def _get_actions_runs(self, **kwargs) -> Dict[str, Any]:
        """Get GitHub Actions workflow runs"""
        repo_name = kwargs.get("repo", "")
        max_runs = kwargs.get("max_runs", 30)

        repo = self.client.get_repo(repo_name)
        runs = repo.get_workflow_runs()

        run_list = []
        for i, run in enumerate(runs):
            if i >= max_runs:
                break
            run_list.append({
                "id": run.id,
                "name": run.name,
                "status": run.status,
                "conclusion": run.conclusion,
                "created_at": run.created_at.isoformat(),
                "url": run.html_url
            })

        return {
            "status": "success",
            "runs": run_list,
            "count": len(run_list)
        }
