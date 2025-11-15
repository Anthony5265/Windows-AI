#!/usr/bin/env python3
"""Summarize local environment provisioning status against roadmap targets."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, List


class Status(str, Enum):
    """Discrete status buckets for environment checks."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class CheckResult:
    """Container for the result of a single environment check."""

    name: str
    status: Status
    details: str
    remediation: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an environment provisioning scorecard."
    )
    parser.add_argument(
        "--venv-path",
        default=".venv",
        help="Path to the Python virtual environment to evaluate (default: .venv).",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Python interpreter expected to exist on the host (default: python).",
    )
    parser.add_argument(
        "--requirements",
        action="append",
        help=(
            "Requirements file(s) that should exist. If omitted, common files such as "
            "requirements.txt and requirements-dev.txt are detected automatically."
        ),
    )
    parser.add_argument(
        "--node-working-dir",
        default=Path.cwd(),
        type=Path,
        help="Directory expected to contain package.json and node_modules.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format for the scorecard (default: text).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the rendered scorecard instead of stdout.",
    )
    return parser.parse_args()


def resolve_requirements(args: argparse.Namespace) -> List[Path]:
    if args.requirements:
        return [Path(path) for path in args.requirements]

    defaults: List[str] = [
        "requirements.txt",
        "requirements-dev.txt",
        "requirements.lock",
        "requirements-test.txt",
    ]
    return [Path(path) for path in defaults]


def check_python_interpreter(executable: str) -> CheckResult:
    location = shutil.which(executable)
    if location is None and Path(executable).exists():
        location = str(Path(executable).resolve())

    if location is None:
        return CheckResult(
            name="Python Interpreter",
            status=Status.FAIL,
            details=f"Interpreter '{executable}' was not found in PATH.",
            remediation="Install Python or update PATH so the interpreter is discoverable.",
        )

    try:
        version = subprocess.check_output([location, "--version"], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return CheckResult(
            name="Python Interpreter",
            status=Status.FAIL,
            details=f"Unable to execute '{location} --version': {exc}",
            remediation="Verify that the interpreter is executable and functioning correctly.",
        )

    return CheckResult(
        name="Python Interpreter",
        status=Status.PASS,
        details=f"Found interpreter at {location} ({version}).",
    )


def check_virtualenv(venv_path: Path) -> CheckResult:
    if not venv_path.exists():
        return CheckResult(
            name="Python Virtualenv",
            status=Status.WARN,
            details=f"Virtual environment not found at {venv_path}.",
            remediation="Run scripts/dev/bootstrap_env.py to create the virtual environment.",
        )

    pyvenv_cfg = venv_path / "pyvenv.cfg"
    pip_executable = venv_path / ("Scripts" if os.name == "nt" else "bin") / "pip"

    missing: list[str] = []
    if not pyvenv_cfg.exists():
        missing.append("pyvenv.cfg")
    if not pip_executable.exists():
        missing.append(str(pip_executable.relative_to(venv_path)))

    if missing:
        return CheckResult(
            name="Python Virtualenv",
            status=Status.FAIL,
            details=f"Virtual environment at {venv_path} is missing {', '.join(missing)}.",
            remediation="Recreate the environment to restore required files.",
        )

    return CheckResult(
        name="Python Virtualenv",
        status=Status.PASS,
        details=f"Virtual environment appears healthy at {venv_path}.",
    )


def check_requirements_files(requirements: Iterable[Path]) -> CheckResult:
    missing: list[str] = []
    empty: list[str] = []

    for path in requirements:
        if not path.exists():
            missing.append(str(path))
            continue
        if path.is_file() and path.stat().st_size == 0:
            empty.append(str(path))

    if missing:
        return CheckResult(
            name="Python Requirements",
            status=Status.WARN,
            details="Missing requirements file(s): " + ", ".join(missing),
            remediation="Check the repository setup or regenerate the missing files.",
        )

    if empty:
        return CheckResult(
            name="Python Requirements",
            status=Status.WARN,
            details="Detected empty requirements file(s): " + ", ".join(empty),
            remediation="Populate the file(s) with the expected dependencies.",
        )

    return CheckResult(
        name="Python Requirements",
        status=Status.PASS,
        details="All referenced requirements files exist and are non-empty.",
    )


def check_node_tooling(node_dir: Path) -> list[CheckResult]:
    results: list[CheckResult] = []

    node_path = shutil.which("node")
    if node_path:
        try:
            node_version = subprocess.check_output([node_path, "--version"], text=True).strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            results.append(
                CheckResult(
                    name="Node.js",
                    status=Status.FAIL,
                    details=f"Unable to execute 'node --version': {exc}",
                    remediation="Reinstall Node.js to ensure the binary works as expected.",
                )
            )
        else:
            results.append(
                CheckResult(
                    name="Node.js",
                    status=Status.PASS,
                    details=f"Found Node.js at {node_path} ({node_version}).",
                )
            )
    else:
        results.append(
            CheckResult(
                name="Node.js",
                status=Status.FAIL,
                details="Node.js executable not found in PATH.",
                remediation="Install Node.js or update PATH to include the Node.js binary.",
            )
        )

    npm_path = shutil.which("npm")
    if npm_path:
        try:
            npm_version = subprocess.check_output([npm_path, "--version"], text=True).strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            results.append(
                CheckResult(
                    name="npm",
                    status=Status.FAIL,
                    details=f"Unable to execute 'npm --version': {exc}",
                    remediation="Reinstall Node.js/npm so the CLI is operational.",
                )
            )
        else:
            results.append(
                CheckResult(
                    name="npm",
                    status=Status.PASS,
                    details=f"Found npm at {npm_path} (version {npm_version}).",
                )
            )
    else:
        results.append(
            CheckResult(
                name="npm",
                status=Status.FAIL,
                details="npm executable not found in PATH.",
                remediation="Install Node.js or adjust PATH to expose npm.",
            )
        )

    package_json = node_dir / "package.json"
    if package_json.exists():
        results.append(
            CheckResult(
                name="package.json",
                status=Status.PASS,
                details=f"Found package.json at {package_json}.",
            )
        )
    else:
        results.append(
            CheckResult(
                name="package.json",
                status=Status.WARN,
                details=f"No package.json in {node_dir}.",
                remediation="Initialize the Node.js workspace or adjust --node-working-dir.",
            )
        )

    node_modules = node_dir / "node_modules"
    if node_modules.exists() and any(node_modules.iterdir()):
        results.append(
            CheckResult(
                name="node_modules",
                status=Status.PASS,
                details=f"node_modules directory populated at {node_modules}.",
            )
        )
    elif node_modules.exists():
        results.append(
            CheckResult(
                name="node_modules",
                status=Status.WARN,
                details=f"node_modules directory at {node_modules} is empty.",
                remediation="Run npm install or npm ci to install dependencies.",
            )
        )
    else:
        results.append(
            CheckResult(
                name="node_modules",
                status=Status.WARN,
                details=f"node_modules directory not found in {node_dir}.",
                remediation="Run npm install or npm ci to populate dependencies.",
            )
        )

    lockfile = node_dir / "package-lock.json"
    if lockfile.exists():
        results.append(
            CheckResult(
                name="package-lock.json",
                status=Status.PASS,
                details=f"Found lockfile at {lockfile}.",
            )
        )
    else:
        results.append(
            CheckResult(
                name="package-lock.json",
                status=Status.WARN,
                details=f"No package-lock.json detected in {node_dir}.",
                remediation="Generate a lockfile with npm install or npm ci to ensure deterministic installs.",
            )
        )

    return results


def aggregate_results(results: Iterable[CheckResult]) -> dict[str, int]:
    totals = {status: 0 for status in Status}
    for result in results:
        totals[result.status] += 1
    return {status.value: count for status, count in totals.items()}


def format_text(results: list[CheckResult]) -> str:
    lines: list[str] = []
    totals = aggregate_results(results)
    lines.append("Environment Scorecard")
    lines.append("=====================")
    lines.append(
        "Summary: "
        + ", ".join(f"{status.upper()}: {count}" for status, count in totals.items())
    )
    lines.append("")

    for result in results:
        lines.append(f"- {result.name}: {result.status.value.upper()}")
        lines.append(f"  Details: {result.details}")
        if result.remediation:
            lines.append(f"  Remediation: {result.remediation}")
    return "\n".join(lines)


def format_markdown(results: list[CheckResult]) -> str:
    totals = aggregate_results(results)
    summary = " | ".join(f"{status.upper()}: {count}" for status, count in totals.items())
    lines = ["# Environment Scorecard", "", f"**Summary:** {summary}", ""]
    lines.append("| Check | Status | Details | Remediation |")
    lines.append("| --- | --- | --- | --- |")
    for result in results:
        remediation = result.remediation or "—"
        lines.append(
            f"| {result.name} | {result.status.value.upper()} | {result.details} | {remediation} |"
        )
    return "\n".join(lines)


def format_json(results: list[CheckResult]) -> str:
    payload = {
        "summary": aggregate_results(results),
        "checks": [
            {
                "name": result.name,
                "status": result.status.value,
                "details": result.details,
                "remediation": result.remediation,
            }
            for result in results
        ],
    }
    return json.dumps(payload, indent=2)


def render_results(results: list[CheckResult], output_format: str) -> str:
    if output_format == "markdown":
        return format_markdown(results)
    if output_format == "json":
        return format_json(results)
    return format_text(results)


def emit_output(text: str, destination: Path | None) -> None:
    if destination is None:
        print(text)
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    content = text if text.endswith("\n") else text + "\n"
    destination.write_text(content, encoding="utf-8")
    print(f"Wrote output to {destination}")


def main() -> None:
    args = parse_args()
    venv_path = Path(args.venv_path)
    requirements = resolve_requirements(args)

    all_results: list[CheckResult] = []
    all_results.append(check_python_interpreter(args.python))
    all_results.append(check_virtualenv(venv_path))
    all_results.append(check_requirements_files(requirements))
    all_results.extend(check_node_tooling(Path(args.node_working_dir)))

    output = render_results(all_results, args.format)
    emit_output(output, args.output)


if __name__ == "__main__":
    main()
