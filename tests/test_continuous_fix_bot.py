from __future__ import annotations

from pathlib import Path

import json

import pytest

try:
    from automation.continuous_fix_bot import (
        CommandResult,
        Task,
        load_config,
        run_task,
    )
except ImportError:
    pytest.skip("backends module not available in this environment", allow_module_level=True)


def write_config(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_load_config_parses_tasks(tmp_path: Path) -> None:
    config_path = write_config(
        tmp_path,
        {
            "interval": 10,
            "tasks": [
                {"name": "pytest", "check": ["npm", "test"]},
                {
                    "name": "lint",
                    "check": ["npm", "run", "lint"],
                    "fix": [["npm", "run", "lint", "--", "--fix"]],
                    "env": {"NODE_ENV": "test"},
                },
            ],
        },
    )

    interval, tasks = load_config(config_path)

    assert interval == 10
    assert [task.name for task in tasks] == ["pytest", "lint"]
    assert tasks[0].check == ("npm", "test")
    assert tasks[1].fixes == (("npm", "run", "lint", "--", "--fix"),)
    assert tasks[1].env == {"NODE_ENV": "test"}


def test_load_config_requires_tasks(tmp_path: Path) -> None:
    config_path = write_config(tmp_path, {"tasks": []})

    with pytest.raises(ValueError):
        load_config(config_path)


def test_run_task_success() -> None:
    task = Task(name="pytest", check=("npm", "test"))

    calls: list[tuple[tuple[str, ...], dict[str, object]]] = []

    def runner(command, *, cwd=None, env=None):
        calls.append((tuple(command), {"cwd": cwd, "env": env}))
        return CommandResult(returncode=0, stdout="ok")

    assert run_task(task, runner=runner) is True
    assert calls == [(("npm", "test"), {"cwd": None, "env": None})]


def test_run_task_fix_applied() -> None:
    task = Task(
        name="lint",
        check=("npm", "run", "lint"),
        fixes=(("npm", "run", "lint", "--", "--fix"),),
    )

    responses = [
        CommandResult(returncode=1, stderr="lint errors"),
        CommandResult(returncode=0, stdout="fixed"),
        CommandResult(returncode=0, stdout="clean"),
    ]

    def runner(command, *, cwd=None, env=None):
        return responses.pop(0)

    assert run_task(task, runner=runner) is True
    assert not responses


def test_run_task_fix_failure() -> None:
    task = Task(
        name="lint",
        check=("npm", "run", "lint"),
        fixes=(("npm", "run", "lint", "--", "--fix"),),
    )

    responses = [
        CommandResult(returncode=1, stderr="lint errors"),
        CommandResult(returncode=2, stderr="fix failed"),
    ]

    def runner(command, *, cwd=None, env=None):
        return responses.pop(0)

    assert run_task(task, runner=runner) is False
    assert not responses
