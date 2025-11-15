#!/usr/bin/env python3
"""Unified command-line interface for environment provisioning utilities."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bootstrap_env  # noqa: E402
import environment_dashboard  # noqa: E402
import environment_roadmap  # noqa: E402
import environment_scorecard  # noqa: E402


def add_bootstrap_subparser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser(
        "bootstrap",
        help="Create or refresh the local Python and Node.js environments.",
        description=(
            "Create the Python virtual environment, install requirements, and "
            "optionally install Node.js dependencies."
        ),
    )
    parser.add_argument(
        "--venv-path",
        default=".venv",
        help="Path for the Python virtual environment (default: .venv).",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter used to create the virtual environment.",
    )
    parser.add_argument(
        "--requirements",
        action="append",
        default=["requirements.txt"],
        help=(
            "Path(s) to requirements files installed after the virtual environment is created. "
            "May be specified multiple times."
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
        help="Directory where npm commands will be executed.",
    )
    parser.add_argument(
        "--npm-command",
        choices=["npm ci", "npm install"],
        default=None,
        help="Override npm command. If omitted the script chooses automatically.",
    )
    parser.set_defaults(handler=handle_bootstrap)


def add_scorecard_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "scorecard",
        help="Run environment verification checks and render a scorecard.",
    )
    parser.add_argument(
        "--venv-path",
        default=".venv",
        help="Path to the Python virtual environment to evaluate (default: .venv).",
    )
    parser.add_argument(
        "--python",
        default="python",
        help="Python interpreter expected to exist on the host.",
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
    parser.set_defaults(handler=handle_scorecard)


def add_roadmap_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "roadmap",
        help="Parse roadmap milestones to surface environment commitments.",
    )
    parser.add_argument(
        "--roadmap",
        type=Path,
        default=Path("docs/ROADMAP.md"),
        help="Path to the roadmap markdown file (default: docs/ROADMAP.md).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format for the alignment report (default: text).",
    )
    parser.add_argument(
        "--keyword",
        default="environment",
        help="Keyword to filter roadmap items (default: environment).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the rendered report instead of stdout.",
    )
    parser.set_defaults(handler=handle_roadmap)


def add_dashboard_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    parser = subparsers.add_parser(
        "dashboard",
        help="Combine scorecard checks with roadmap alignment data.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        help="Output format for the dashboard (default: text).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the rendered dashboard instead of stdout.",
    )
    parser.add_argument(
        "--skip-scorecard",
        action="store_true",
        help="Skip collecting local environment scorecard details.",
    )
    parser.add_argument(
        "--venv-path",
        type=Path,
        default=Path(".venv"),
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
        type=Path,
        help=(
            "Requirements file(s) that should exist. If omitted, common files are detected automatically."
        ),
    )
    parser.add_argument(
        "--node-working-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory expected to contain package.json and node_modules.",
    )
    parser.add_argument(
        "--skip-roadmap",
        action="store_true",
        help="Skip parsing roadmap milestones.",
    )
    parser.add_argument(
        "--roadmap",
        type=Path,
        default=Path("docs/ROADMAP.md"),
        help="Path to the roadmap markdown file (default: docs/ROADMAP.md).",
    )
    parser.add_argument(
        "--keyword",
        default="environment",
        help="Keyword to filter roadmap items (default: environment).",
    )
    parser.set_defaults(handler=handle_dashboard)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified interface for environment provisioning workflows.",
    )
    subparsers = parser.add_subparsers(dest="command")
    add_bootstrap_subparser(subparsers)
    add_scorecard_subparser(subparsers)
    add_roadmap_subparser(subparsers)
    add_dashboard_subparser(subparsers)
    return parser


def handle_bootstrap(args: argparse.Namespace) -> None:
    bootstrap_env.ensure_python_env(args)
    bootstrap_env.ensure_node_env(args)
    print("Environment bootstrap completed successfully.")


def handle_scorecard(args: argparse.Namespace) -> None:
    requirements = environment_scorecard.resolve_requirements(args)
    results = [
        environment_scorecard.check_python_interpreter(args.python),
        environment_scorecard.check_virtualenv(Path(args.venv_path)),
        environment_scorecard.check_requirements_files(requirements),
    ]
    results.extend(environment_scorecard.check_node_tooling(Path(args.node_working_dir)))
    output = environment_scorecard.render_results(results, args.format)
    environment_scorecard.emit_output(output, args.output)


def handle_roadmap(args: argparse.Namespace) -> None:
    phases = environment_roadmap.parse_roadmap(args.roadmap, args.keyword)
    output = environment_roadmap.render(phases, args.format)
    environment_roadmap.emit_output(output, args.output)


def handle_dashboard(args: argparse.Namespace) -> None:
    scorecard_results = environment_dashboard.collect_scorecard_results(args)
    phases = environment_dashboard.collect_roadmap_phases(args)
    output = environment_dashboard.render(scorecard_results, phases, args.format)
    environment_dashboard.emit_output(output, args.output)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "handler"):
        parser.print_help()
        return 1

    try:
        args.handler(args)
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode
    except Exception as exc:  # pragma: no cover - CLI entrypoint
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
