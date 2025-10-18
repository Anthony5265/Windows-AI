"""Utility bot that continuously runs repo health checks and auto-fix steps.

This module exposes a small framework for defining *tasks* that keep the
repository healthy.  Each task specifies a ``check`` command that validates a
particular subsystem (tests, linters, etc.) and optional ``fix`` commands that
are executed when the check fails.  The bot iterates over the configured tasks
forever (or for a caller-specified number of iterations) with a delay between
cycles so it can be used as a long-running maintenance helper.

Example configuration file (JSON)::

    {
      "interval": 900,
      "tasks": [
        {
          "name": "pytest",
          "check": ["npm", "test", "--", "--maxfail=1"]
        },
        {
          "name": "lint",
          "check": ["npm", "run", "lint"],
          "fix": [["npm", "run", "lint", "--", "--fix"]]
        }
      ]
    }

The CLI entry point (``python -m automation.continuous_fix_bot``) accepts the
path to the configuration file, how frequently the bot should run, and whether
it should only execute a single cycle.  The implementation is deliberately
dependency-free so it can run anywhere Python is available (CI runners,
developer machines, or long-lived automation hosts).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, MutableSequence, Sequence


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommandResult:
    """Normalized representation of a finished subprocess command."""

    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        """Return ``True`` when the command completed successfully."""

        return self.returncode == 0


@dataclass(frozen=True)
class Task:
    """Description of a maintenance task for the bot to execute."""

    name: str
    check: Sequence[str]
    fixes: tuple[Sequence[str], ...] = field(default_factory=tuple)
    cwd: Path | None = None
    env: Mapping[str, str] | None = None

    def describe(self) -> str:
        """Return a human readable summary used in logs."""

        return f"Task(name={self.name!r}, check={list(self.check)!r})"


def run_subprocess(
    command: Sequence[str],
    *,
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> CommandResult:
    """Execute ``command`` and return a :class:`CommandResult` instance."""

    LOGGER.debug("Running command %s (cwd=%s)", command, cwd)
    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)

    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env_vars,
        capture_output=True,
        text=True,
        check=False,
    )
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def _coerce_command(value: Iterable[str], *, field_name: str, task_name: str) -> tuple[str, ...]:
    try:
        command = tuple(str(part) for part in value)
    except TypeError as exc:  # pragma: no cover - defensive guard.
        raise ValueError(f"{field_name} for task {task_name!r} must be a sequence") from exc

    if not command:
        raise ValueError(f"{field_name} for task {task_name!r} cannot be empty")

    return command


def load_config(config_path: Path) -> tuple[int, list[Task]]:
    """Load a configuration file from ``config_path``.

    Returns a tuple of ``(interval_seconds, tasks)``.
    """

    with config_path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)

    interval = int(raw.get("interval", 900))
    if interval < 0:
        raise ValueError("interval cannot be negative")

    raw_tasks = raw.get("tasks", [])
    if not isinstance(raw_tasks, list) or not raw_tasks:
        raise ValueError("configuration must include at least one task")

    tasks: list[Task] = []
    for raw_task in raw_tasks:
        if not isinstance(raw_task, Mapping):
            raise ValueError("each task must be a mapping")

        name = str(raw_task.get("name") or "task")
        check = _coerce_command(raw_task.get("check", ()), field_name="check", task_name=name)
        fixes_raw = raw_task.get("fix") or []
        if isinstance(fixes_raw, Mapping):
            raise ValueError("fix must be a sequence of commands")

        fixes: MutableSequence[Sequence[str]] = []
        for fix in fixes_raw:
            fixes.append(
                _coerce_command(fix, field_name="fix", task_name=name),
            )

        cwd_value = raw_task.get("cwd")
        cwd = Path(cwd_value).resolve() if cwd_value else None
        env_raw = raw_task.get("env")
        env = {str(key): str(value) for key, value in env_raw.items()} if isinstance(env_raw, Mapping) else None

        tasks.append(Task(name=name, check=check, fixes=tuple(fixes), cwd=cwd, env=env))

    return interval, tasks


def run_task(task: Task, *, runner=run_subprocess) -> bool:
    """Execute a task, running fixes when the check fails.

    Returns ``True`` when the task completes successfully after fixes
    (if any) and ``False`` otherwise.
    """

    LOGGER.info("Running %s", task.describe())
    result = runner(task.check, cwd=task.cwd, env=task.env)

    if result.ok:
        LOGGER.info("%s succeeded", task.name)
        return True

    LOGGER.warning(
        "%s failed with code %s\nstdout:%s\nstderr:%s",
        task.name,
        result.returncode,
        result.stdout.strip(),
        result.stderr.strip(),
    )

    if not task.fixes:
        LOGGER.error("No fixes defined for %s", task.name)
        return False

    for fix_command in task.fixes:
        LOGGER.info("Running fix for %s: %s", task.name, list(fix_command))
        fix_result = runner(fix_command, cwd=task.cwd, env=task.env)
        if not fix_result.ok:
            LOGGER.error(
                "Fix command %s failed with code %s", list(fix_command), fix_result.returncode
            )
            return False

    LOGGER.info("Re-running check for %s after fixes", task.name)
    retry_result = runner(task.check, cwd=task.cwd, env=task.env)
    if retry_result.ok:
        LOGGER.info("%s succeeded after fixes", task.name)
        return True

    LOGGER.error(
        "%s still failing after fixes (code %s)", task.name, retry_result.returncode
    )
    return False


def _create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Continuous repository fix bot")
    parser.add_argument(
        "--config",
        default=Path("config/fix_bot.json"),
        type=Path,
        help="Path to the JSON configuration file.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=None,
        help="Override the interval (seconds) between runs.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single cycle instead of looping forever.",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="Stop the bot after this many cycles.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (e.g. INFO, DEBUG).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _create_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=args.log_level.upper(), format="[%(levelname)s] %(message)s")

    config_path = args.config
    if not config_path.exists():
        parser.error(f"configuration file {config_path} does not exist")

    interval, tasks = load_config(config_path)
    if args.interval is not None:
        interval = args.interval

    run_count = 0
    while True:
        run_count += 1
        LOGGER.info("Starting maintenance cycle %s", run_count)
        all_ok = True
        for task in tasks:
            ok = run_task(task)
            all_ok = all_ok and ok

        if args.once:
            return 0 if all_ok else 1

        if args.max_runs is not None and run_count >= args.max_runs:
            return 0 if all_ok else 1

        if interval == 0:
            continue

        LOGGER.debug("Sleeping for %s seconds before next cycle", interval)
        time.sleep(interval)


if __name__ == "__main__":
    sys.exit(main())
