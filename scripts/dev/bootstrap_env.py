#!/usr/bin/env python3
"""Utility for bootstrapping Python and Node.js development environments.

This script creates a local Python virtual environment, installs required
packages, and optionally prepares the Node.js workspace using npm.  The goal is
for contributors to have a single, reproducible entry point that aligns with
the Phase 1 roadmap expectations.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap Python virtualenv and Node.js dependencies in one command.",
    )
    parser.add_argument(
        "--venv-path",
        default=".venv",
        help="Path where the Python virtual environment will be created (default: .venv).",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter used to create the virtual environment (default: current interpreter).",
    )
    parser.add_argument(
        "--requirements",
        action="append",
        default=["requirements.txt"],
        help=(
            "Path(s) to requirements files installed after the virtual environment is created. "
            "May be provided multiple times."
        ),
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate the virtual environment even if it already exists.",
    )
    parser.add_argument(
        "--skip-python",
        action="store_true",
        help="Skip Python environment setup.",
    )
    parser.add_argument(
        "--skip-node",
        action="store_true",
        help="Skip Node.js dependency installation.",
    )
    parser.add_argument(
        "--node-working-dir",
        default=Path.cwd(),
        type=Path,
        help="Directory where npm will be executed (default: repository root).",
    )
    parser.add_argument(
        "--npm-command",
        choices=["npm ci", "npm install"],
        default=None,
        help="Override npm command. If omitted the script chooses automatically.",
    )
    return parser.parse_args()


def run_command(command: Iterable[str], cwd: Path | None = None) -> None:
    display = " ".join(command)
    location = f" (cwd={cwd})" if cwd else ""
    print(f"-> {display}{location}")
    subprocess.check_call(list(command), cwd=str(cwd) if cwd else None)


def ensure_python_env(args: argparse.Namespace) -> None:
    venv_path = Path(args.venv_path)
    if args.recreate and venv_path.exists():
        print(f"Removing existing virtual environment at {venv_path}")
        shutil.rmtree(venv_path)

    if args.skip_python:
        print("Skipping Python environment setup as requested.")
        return

    if not venv_path.exists():
        print(f"Creating virtual environment at {venv_path} using {args.python}")
        run_command([args.python, "-m", "venv", str(venv_path)])
    else:
        print(f"Virtual environment already exists at {venv_path}; skipping creation.")

    pip_executable = venv_path / ("Scripts" if os.name == "nt" else "bin") / "pip"
    if not pip_executable.exists():
        raise RuntimeError(
            f"Unable to locate pip executable inside virtual environment at {pip_executable}."
        )

    for requirement in args.requirements:
        requirement_path = Path(requirement)
        if not requirement_path.exists():
            print(f"! Skipping missing requirements file: {requirement_path}")
            continue
        print(f"Installing Python requirements from {requirement_path}")
        run_command([str(pip_executable), "install", "-r", str(requirement_path)])


def ensure_node_env(args: argparse.Namespace) -> None:
    if args.skip_node:
        print("Skipping Node.js dependency installation as requested.")
        return

    node_dir = Path(args.node_working_dir).resolve()
    if not node_dir.exists():
        raise FileNotFoundError(f"Node working directory does not exist: {node_dir}")

    package_json = node_dir / "package.json"
    if not package_json.exists():
        print(f"! No package.json found in {node_dir}; skipping npm install.")
        return

    lockfile = node_dir / "package-lock.json"
    default_command = "npm ci" if lockfile.exists() else "npm install"
    npm_command = args.npm_command or default_command

    print(f"Installing Node.js dependencies with `{npm_command}` in {node_dir}")
    run_command(npm_command.split(), cwd=node_dir)


def main() -> None:
    args = parse_args()
    try:
        ensure_python_env(args)
        ensure_node_env(args)
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}")
        sys.exit(exc.returncode)
    except Exception as exc:  # pragma: no cover - bootstrap scripts often run manually
        print(f"Error: {exc}")
        sys.exit(1)
    else:
        print("Environment bootstrap completed successfully.")


if __name__ == "__main__":
    main()
