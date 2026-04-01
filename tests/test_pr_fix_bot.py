from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
try:
    from automation.pr_fix_bot import (
        PRFixBot,
        PRFixBotConfig,
        PullRequestInfo,
        GitHubClient,
        load_pr_bot_config,
    )
    from automation.continuous_fix_bot import Task
except ImportError:
    pytest.skip("backends module not available in this environment", allow_module_level=True)


def write_config(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def make_pull(number: int) -> dict:
    return {
        "number": number,
        "title": f"Update #{number}",
        "head": {
            "ref": f"feature-{number}",
            "repo": {
                "full_name": "example/repo",
                "clone_url": "https://github.com/example/repo.git",
            },
        },
        "maintainer_can_modify": True,
        "html_url": f"https://github.com/example/repo/pull/{number}",
    }


def test_load_pr_bot_config(tmp_path: Path) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    config_path = write_config(
        tmp_path,
        {
            "repo": "example/repo",
            "remote": "origin",
            "token_env": "GITHUB_TOKEN",
            "commit_message": "auto {pr_number}",
            "workdir": str(repo_path),
            "push": False,
            "tasks": [
                {"name": "lint", "check": ["npm", "run", "lint"]},
                {
                    "name": "fix-lint",
                    "check": ["npm", "run", "lint"],
                    "fix": [["npm", "run", "lint", "--", "--fix"]],
                },
            ],
        },
    )

    config, tasks = load_pr_bot_config(config_path)

    assert config.repo == "example/repo"
    assert config.remote == "origin"
    assert config.commit_message == "auto {pr_number}"
    assert config.workdir == repo_path.resolve()
    assert config.push is False
    assert [task.name for task in tasks] == ["lint", "fix-lint"]
    assert tasks[1].fixes == (("npm", "run", "lint", "--", "--fix"),)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.status_code = 200

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("error")


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.calls: list[tuple[str, dict]] = []
        self.headers: dict[str, str] = {}

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params))
        return self.responses.pop(0)


def test_github_client_paginates_and_limits() -> None:
    session = FakeSession(
        [
            FakeResponse([make_pull(1)]),
            FakeResponse([make_pull(2)]),
            FakeResponse([]),
        ]
    )
    client = GitHubClient(token=None, base_url="https://api.example.com", session=session)

    pulls = client.list_open_pull_requests("example/repo", per_page=1, max_items=2)

    assert len(pulls) == 2
    assert session.calls == [
        ("https://api.example.com/repos/example/repo/pulls", {"state": "open", "per_page": 1, "page": 1}),
        ("https://api.example.com/repos/example/repo/pulls", {"state": "open", "per_page": 1, "page": 2}),
    ]


class FakeGit:
    def __init__(self):
        self.branch = "main"
        self.commit = "abc123"
        self.status = " M file\n"
        self.commands: list[tuple[str, ...]] = []
        self.last_commit_message: str | None = None
        self.last_push: tuple[str, ...] | None = None
        self.deleted: list[str] = []

    def __call__(self, command, *, cwd, capture_output=False, check=True):
        args = tuple(command[1:])
        self.commands.append(args)
        if args == ("rev-parse", "HEAD"):
            return SimpleNamespace(stdout=self.commit + "\n", stderr="", returncode=0)
        if args == ("rev-parse", "--abbrev-ref", "HEAD"):
            return SimpleNamespace(stdout=self.branch + "\n", stderr="", returncode=0)
        if args and args[0] == "fetch":
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if args and args[0] == "checkout":
            if len(args) > 1:
                self.branch = args[1]
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if args == ("status", "--porcelain"):
            return SimpleNamespace(stdout=self.status, stderr="", returncode=0)
        if args and args[0] == "add":
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if args and args[0] == "commit":
            self.last_commit_message = args[-1]
            self.status = ""
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if args and args[0] == "push":
            self.last_push = args[1:]
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if args == ("reset", "--hard", "HEAD"):
            self.status = ""
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if args == ("clean", "-fd"):
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        if args[:2] == ("branch", "-D"):
            if len(args) > 2:
                self.deleted.append(args[2])
            return SimpleNamespace(stdout="", stderr="", returncode=0)
        return SimpleNamespace(stdout="", stderr="", returncode=0)


def test_process_pull_request_commits_and_pushes(tmp_path: Path) -> None:
    config = PRFixBotConfig(
        repo="example/repo",
        remote="origin",
        workdir=tmp_path,
        push=True,
    )
    git = FakeGit()

    pr = PullRequestInfo(
        number=5,
        title="Improve lint",
        head_ref="feature-5",
        head_repo_full_name="example/repo",
        head_repo_clone_url="https://github.com/example/repo.git",
        maintainer_can_modify=True,
        html_url="https://github.com/example/repo/pull/5",
    )

    bot = PRFixBot(config, [Task(name="lint", check=("npm", "run", "lint"))], token="", git_runner=git)
    result = bot.process_pull_request(pr, task_runner=lambda task, runner: True)

    assert result is True
    assert ("fetch", "origin", "pull/5/head:pr-5") in git.commands
    assert ("checkout", "pr-5") in git.commands
    assert ("status", "--porcelain") in git.commands
    assert ("commit", "-m", "chore: auto-fix PR #5") in git.commands
    assert git.last_push == ("origin", "HEAD:feature-5")
    assert git.branch == "main"
    assert "pr-5" in git.deleted


def test_process_pull_request_failure_resets(tmp_path: Path) -> None:
    config = PRFixBotConfig(repo="example/repo", remote="origin", workdir=tmp_path, push=False)
    git = FakeGit()

    bot = PRFixBot(config, [Task(name="lint", check=("npm", "run", "lint"))], token=None, git_runner=git)
    result = bot.process_pull_request(
        PullRequestInfo(
            number=2,
            title="Broken",
            head_ref="feature-2",
            head_repo_full_name="example/repo",
            head_repo_clone_url="https://github.com/example/repo.git",
            maintainer_can_modify=True,
            html_url="https://github.com/example/repo/pull/2",
        ),
        task_runner=lambda task, runner: False,
    )

    assert result is False
    assert ("reset", "--hard", "HEAD") in git.commands
    assert ("clean", "-fd") in git.commands
    assert all(cmd[0] != "commit" for cmd in git.commands)
