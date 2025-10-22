from __future__ import annotations

from pathlib import Path

from workflows import WorkflowCatalog, WorkflowRunner


WORKFLOW_TEMPLATE = """
---
id: {id}
title: {title}
tags: {tags}
description: {description}
inputs:
{inputs}
run:
{run}
"""


def write_workflow(path: Path, *, run_block: str, inputs_block: str = "  - name: placeholder\n    type: string\n    default: value\n") -> None:
    path.write_text(
        WORKFLOW_TEMPLATE.format(
            id=path.stem,
            title=path.stem.replace("-", " ").title(),
            tags="[\"test\"]",
            description="Sample workflow",
            inputs=inputs_block,
            run=run_block,
        ),
        encoding="utf-8",
    )


def test_catalog_loads_and_searches(tmp_path: Path) -> None:
    shell = tmp_path / "shell.yml"
    script_dir = tmp_path / "nested"
    script_dir.mkdir()
    script = script_dir / "script.yml"

    write_workflow(
        shell,
        run_block="  mode: shell\n  command: \"echo ready\"\n",
    )
    write_workflow(
        script,
        run_block="  mode: script\n  script:\n    language: python\n    content: |\n      print(\"hello\")\n",
    )

    catalog = WorkflowCatalog(root=tmp_path)
    ids = sorted(spec.id for spec in catalog.list())
    assert ids == ["script", "shell"]

    result = catalog.search("shell")
    assert result and result[0].id == "shell"


def test_runner_executes_all_modes(tmp_path: Path) -> None:
    shell = tmp_path / "hello.yml"
    script = tmp_path / "numbers.yml"
    action = tmp_path / "action.yml"

    write_workflow(
        shell,
        run_block="  mode: shell\n  command: \"echo ${{name}}\"\n",
        inputs_block="  - name: name\n    type: string\n    default: hi\n",
    )

    write_workflow(
        script,
        run_block=(
            "  mode: script\n  script:\n    language: python\n    content: |\n      from pathlib import Path\n"
            "      target = Path(r'${{target}}')\n      target.write_text('done', encoding='utf-8')\n"
            "      print('script-finished')\n"
        ),
        inputs_block="  - name: target\n    type: path\n    default: \"" + str(tmp_path / "out.txt") + "\"\n",
    )

    write_workflow(
        action,
        run_block=(
            "  mode: action\n  action:\n    name: shell\n    params:\n      command: \"printf 'foo' | tr 'a-z' 'A-Z'\"\n"
        ),
    )

    catalog = WorkflowCatalog(root=tmp_path)
    runner = WorkflowRunner(catalog)

    shell_log = runner.run("hello", overrides={"name": "world"})
    assert shell_log.result == "world"
    assert shell_log.exit_code == 0

    script_log = runner.run("numbers")
    assert "script-finished" in script_log.result
    assert (tmp_path / "out.txt").read_text(encoding="utf-8") == "done"

    action_log = runner.run("action")
    assert action_log.result == {"stdout": "FOO"}

    assert {log.id for log in runner.logs} == {"hello", "numbers", "action"}
    assert all(log.duration >= 0 for log in runner.logs)
