"""Bot that automatically applies fixes to open pull requests."""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable, Iterable, Sequence

import requests

from .continuous_fix_bot import CommandResult, Task, parse_tasks, run_subprocess, run_task

LOGGER = logging.getLogger(__name__)


@dataclass
class PRFixBotConfig:
    """Configuration values for the pull request fix bot."""

    repo: str
    remote: str = "origin"
    token_env: str = "GITHUB_TOKEN"
    commit_message: str = "chore: auto-fix PR #{pr_number}"
    workdir: Path = Path(".")
    push: bool = True
    base_url: str = "https://api.github.com"
    per_page: int = 30
    max_prs: int | None = None


@dataclass(frozen=True)
class PullRequestInfo:
    """Normalized representation of a GitHub pull request."""

    number: int
    title: str
    head_ref: str
    head_repo_full_name: str | None
    head_repo_clone_url: str | None
    maintainer_can_modify: bool
    html_url: str

    def is_from_repo(self, repo_full_name: str) -> bool:
        if self.head_repo_full_name is None:
            return False
        return self.head_repo_full_name.lower() == repo_full_name.lower()


class GitHubClient:
    """Minimal wrapper around the GitHub REST API."""

    def __init__(
        self,
        token: str | None,
        *,
        base_url: str = "https://api.github.com",
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        headers = {
            "Accept": "application/vnd.github+json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.session.headers.update(headers)

    def list_open_pull_requests(
        self,
        repo: str,
        *,
        per_page: int = 30,
        max_items: int | None = None,
    ) -> list[PullRequestInfo]:
        """Return open pull requests for ``repo``."""

        url = f"{self.base_url}/repos/{repo}/pulls"
        page = 1
        results: list[PullRequestInfo] = []

        while True:
            params = {"state": "open", "per_page": per_page, "page": page}
            LOGGER.debug("Fetching pull requests from %s with params %s", url, params)
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json() or []
            if not data:
                break

            for item in data:
                results.append(_pull_request_from_api(item))
                if max_items is not None and len(results) >= max_items:
                    return results

            page += 1

        return results


def _pull_request_from_api(data: dict) -> PullRequestInfo:
    head = data.get("head") or {}
    head_repo = head.get("repo") or {}
    return PullRequestInfo(
        number=int(data.get("number", 0)),
        title=str(data.get("title") or ""),
        head_ref=str(head.get("ref") or ""),
        head_repo_full_name=head_repo.get("full_name"),
        head_repo_clone_url=head_repo.get("clone_url"),
        maintainer_can_modify=bool(data.get("maintainer_can_modify")),
        html_url=str(data.get("html_url") or ""),
    )


def load_pr_bot_config(config_path: Path) -> tuple[PRFixBotConfig, list[Task]]:
    """Load configuration and tasks for :class:`PRFixBot`."""

    with config_path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)

    repo = raw.get("repo")
    if not repo:
        raise ValueError("configuration must include a 'repo' field")

    workdir = Path(raw.get("workdir", ".")).resolve()

    config = PRFixBotConfig(
        repo=str(repo),
        remote=str(raw.get("remote", "origin")),
        token_env=str(raw.get("token_env", "GITHUB_TOKEN")),
        commit_message=str(raw.get("commit_message", "chore: auto-fix PR #{pr_number}")),
        workdir=workdir,
        push=bool(raw.get("push", True)),
        base_url=str(raw.get("base_url", "https://api.github.com")),
        per_page=int(raw.get("per_page", 30)),
        max_prs=int(raw["max_prs"]) if raw.get("max_prs") is not None else None,
    )

    tasks = parse_tasks(raw.get("tasks"))

    return config, tasks


def _default_git_runner(
    command: Sequence[str],
    *,
    cwd: Path,
    capture_output: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=capture_output,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            command,
            output=result.stdout,
            stderr=result.stderr,
        )
    return result


class PRFixBot:
    """Apply fix tasks to open pull requests."""

    def __init__(
        self,
        config: PRFixBotConfig,
        tasks: Sequence[Task],
        *,
        token: str | None = None,
        git_runner: Callable[..., subprocess.CompletedProcess] | None = None,
    ) -> None:
        self.config = config
        self.tasks = list(tasks)
        self.token = token
        self.git_runner = git_runner or _default_git_runner
        self.workdir = config.workdir

        if not self.tasks:
            raise ValueError("at least one task must be configured")

    # ---------------------------------------------------------------- git utils
    def run_git(
        self,
        *args: str,
        capture_output: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        command = ["git", *args]
        return self.git_runner(command, cwd=self.workdir, capture_output=capture_output, check=check)

    def _current_commit(self) -> str:
        result = self.run_git("rev-parse", "HEAD", capture_output=True)
        return (result.stdout or "").strip()

    def _current_branch(self) -> str:
        result = self.run_git("rev-parse", "--abbrev-ref", "HEAD", capture_output=True)
        return (result.stdout or "").strip() or "HEAD"

    def _make_runner(self) -> Callable[..., CommandResult]:
        def runner(command: Sequence[str], *, cwd: Path | None = None, env=None) -> CommandResult:
            return run_subprocess(command, cwd=cwd or self.workdir, env=env)

        return runner

    def _has_changes(self) -> bool:
        result = self.run_git("status", "--porcelain", capture_output=True)
        return bool((result.stdout or "").strip())

    def _clean_worktree(self) -> None:
        self.run_git("reset", "--hard", "HEAD", check=False)
        self.run_git("clean", "-fd", check=False)

    def _escape(self, value: str) -> str:
        return value.replace("{", "{{").replace("}", "}}").strip()

    def _commit(self, pr: PullRequestInfo) -> None:
        message = self.config.commit_message.format(
            pr_number=pr.number,
            title=self._escape(pr.title),
        )
        self.run_git("add", "--all")
        self.run_git("commit", "-m", message)

    def _auth_url(self, url: str) -> str:
        if not self.token:
            return url
        if url.startswith("https://"):
            return "https://" + self.token + "@" + url[len("https://") :]
        if url.startswith("http://"):
            return "http://" + self.token + "@" + url[len("http://") :]
        return url

    def _push(self, pr: PullRequestInfo) -> None:
        if not self.config.push:
            LOGGER.info("Push disabled; skipping push for PR #%s", pr.number)
            return

        if pr.is_from_repo(self.config.repo):
            remote = self.config.remote
            self.run_git("push", remote, f"HEAD:{pr.head_ref}")
            return

        if not pr.maintainer_can_modify:
            LOGGER.warning("Cannot push to PR #%s because maintainer modifications are disabled", pr.number)
            return

        if not pr.head_repo_clone_url:
            LOGGER.warning("Cannot push to PR #%s because head repository information is missing", pr.number)
            return

        remote_url = self._auth_url(pr.head_repo_clone_url)
        self.run_git("push", remote_url, f"HEAD:{pr.head_ref}")

    # ------------------------------------------------------------- main routine
    def process_pull_request(
        self,
        pr: PullRequestInfo,
        *,
        dry_run: bool = False,
        task_runner=run_task,
    ) -> bool:
        LOGGER.info("Processing PR #%s (%s)", pr.number, pr.title)

        original_commit = self._current_commit()
        original_branch = self._current_branch()

        local_branch = f"pr-{pr.number}"

        try:
            self.run_git("fetch", self.config.remote, f"pull/{pr.number}/head:{local_branch}")
            self.run_git("checkout", local_branch)
        except subprocess.CalledProcessError as exc:
            LOGGER.error("Failed to fetch PR #%s: %s", pr.number, exc)
            return False

        try:
            runner = self._make_runner()
            all_ok = True
            for task in self.tasks:
                ok = task_runner(task, runner=runner)
                all_ok = all_ok and ok

            if not all_ok:
                LOGGER.error("Tasks failed for PR #%s", pr.number)
                return False

            if dry_run:
                LOGGER.info("Dry run enabled; skipping commit for PR #%s", pr.number)
                return True

            if not self._has_changes():
                LOGGER.info("No changes detected for PR #%s", pr.number)
                return True

            self._commit(pr)
            self._push(pr)
            return True
        except subprocess.CalledProcessError as exc:
            LOGGER.error("Git command failed for PR #%s: %s", pr.number, exc)
            return False
        finally:
            if not dry_run:
                self._clean_worktree()
            try:
                if original_branch != "HEAD":
                    self.run_git("checkout", original_branch, check=False)
                else:
                    self.run_git("checkout", original_commit, check=False)
            finally:
                if local_branch != original_branch:
                    self.run_git("branch", "-D", local_branch, check=False)

    def run(
        self,
        pull_requests: Iterable[PullRequestInfo],
        *,
        dry_run: bool = False,
        task_runner=run_task,
        limit: int | None = None,
    ) -> bool:
        processed = 0
        overall_ok = True
        for pr in pull_requests:
            if limit is not None and processed >= limit:
                break
            ok = self.process_pull_request(pr, dry_run=dry_run, task_runner=task_runner)
            overall_ok = overall_ok and ok
            processed += 1
        return overall_ok


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automatically fix open pull requests")
    parser.add_argument("--config", type=Path, default=Path("config/pr_fix_bot.json"))
    parser.add_argument("--max-prs", type=int, default=None, help="Override the maximum number of PRs to process")
    parser.add_argument("--dry-run", action="store_true", help="Run checks without committing or pushing")
    parser.add_argument("--log-level", default="INFO", help="Logging level (e.g. INFO, DEBUG)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=args.log_level.upper(), format="[%(levelname)s] %(message)s")

    config_path = args.config
    if not config_path.exists():
        parser.error(f"configuration file {config_path} does not exist")

    config, tasks = load_pr_bot_config(config_path)

    limit = args.max_prs if args.max_prs is not None else config.max_prs
    if args.max_prs is not None and config.max_prs is not None:
        config = replace(config, max_prs=args.max_prs)

    token = os.getenv(config.token_env)
    if token:
        LOGGER.debug("Using token from %s", config.token_env)
    else:
        LOGGER.warning("No token found in %s; requests may be rate limited", config.token_env)

    client = GitHubClient(token, base_url=config.base_url)

    prs = client.list_open_pull_requests(
        config.repo,
        per_page=config.per_page,
        max_items=limit,
    )

    if not prs:
        LOGGER.info("No open pull requests found")
        return 0

    bot = PRFixBot(config, tasks, token=token)
    success = bot.run(prs, dry_run=args.dry_run, limit=limit)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
