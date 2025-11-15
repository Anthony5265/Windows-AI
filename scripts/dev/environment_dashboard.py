#!/usr/bin/env python3
"""Combine environment scorecard checks with roadmap alignment insights."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import environment_scorecard  # noqa: E402
import environment_roadmap  # noqa: E402


ScorecardResults = Optional[List[environment_scorecard.CheckResult]]
RoadmapPhases = Optional[List[environment_roadmap.PhaseAlignment]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a unified environment readiness dashboard that merges "
            "local tooling checks with roadmap commitments."
        )
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

    scorecard = parser.add_argument_group("Scorecard options")
    scorecard.add_argument(
        "--skip-scorecard",
        action="store_true",
        help="Skip collecting local environment scorecard details.",
    )
    scorecard.add_argument(
        "--venv-path",
        type=Path,
        default=Path(".venv"),
        help="Path to the Python virtual environment to evaluate (default: .venv).",
    )
    scorecard.add_argument(
        "--python",
        default="python",
        help="Python interpreter expected to exist on the host (default: python).",
    )
    scorecard.add_argument(
        "--requirements",
        action="append",
        type=Path,
        help=(
            "Requirements file(s) that should exist. If omitted, common files "
            "are detected automatically."
        ),
    )
    scorecard.add_argument(
        "--node-working-dir",
        type=Path,
        default=Path.cwd(),
        help="Directory expected to contain package.json and node_modules.",
    )

    roadmap = parser.add_argument_group("Roadmap options")
    roadmap.add_argument(
        "--skip-roadmap",
        action="store_true",
        help="Skip parsing roadmap milestones.",
    )
    roadmap.add_argument(
        "--roadmap",
        type=Path,
        default=Path("docs/ROADMAP.md"),
        help="Path to the roadmap markdown file (default: docs/ROADMAP.md).",
    )
    roadmap.add_argument(
        "--keyword",
        default="environment",
        help=(
            "Keyword to filter roadmap items. Use to explore adjacent focus "
            "areas (default: environment)."
        ),
    )

    return parser.parse_args()


def collect_scorecard_results(args: argparse.Namespace) -> ScorecardResults:
    if args.skip_scorecard:
        return None

    requirements = environment_scorecard.resolve_requirements(args)
    results: list[environment_scorecard.CheckResult] = []
    results.append(environment_scorecard.check_python_interpreter(args.python))
    results.append(environment_scorecard.check_virtualenv(args.venv_path))
    results.append(environment_scorecard.check_requirements_files(requirements))
    results.extend(environment_scorecard.check_node_tooling(args.node_working_dir))
    return results


def collect_roadmap_phases(args: argparse.Namespace) -> RoadmapPhases:
    if args.skip_roadmap:
        return None
    return environment_roadmap.parse_roadmap(args.roadmap, args.keyword)


def format_text(scorecard_results: ScorecardResults, phases: RoadmapPhases) -> str:
    lines: list[str] = [
        "Environment Provisioning Dashboard",
        "=================================",
        "",
    ]

    lines.append("Scorecard")
    lines.append("---------")
    if scorecard_results is None:
        lines.append("Scorecard section skipped by request.")
    else:
        totals = environment_scorecard.aggregate_results(scorecard_results)
        summary = ", ".join(f"{status.upper()}: {count}" for status, count in totals.items())
        lines.append(f"Summary: {summary}")
        lines.append("")
        for result in scorecard_results:
            lines.append(f"- {result.name}: {result.status.value.upper()}")
            lines.append(f"  Details: {result.details}")
            if result.remediation:
                lines.append(f"  Remediation: {result.remediation}")
    lines.append("")

    lines.append("Roadmap Alignment")
    lines.append("-----------------")
    if phases is None:
        lines.append("Roadmap section skipped by request.")
    elif not phases:
        lines.append("No roadmap entries matched the requested keyword.")
    else:
        for phase in phases:
            header = f"{phase.identifier} — {phase.title}"
            lines.append(header)
            lines.append("~" * len(header))
            for section, entries in phase.sections.items():
                lines.append(f"  {section}:")
                for entry in entries:
                    lines.append(f"    - {entry}")
            lines.append("")
    return "\n".join(lines).rstrip()


def format_markdown(scorecard_results: ScorecardResults, phases: RoadmapPhases) -> str:
    lines: list[str] = ["# Environment Provisioning Dashboard", ""]

    lines.append("## Scorecard")
    if scorecard_results is None:
        lines.append("_Scorecard section skipped by request_.")
    else:
        totals = environment_scorecard.aggregate_results(scorecard_results)
        summary = " | ".join(f"{status.upper()}: {count}" for status, count in totals.items())
        lines.append("")
        lines.append(f"**Summary:** {summary}")
        lines.append("")
        lines.append("| Check | Status | Details | Remediation |")
        lines.append("| --- | --- | --- | --- |")
        for result in scorecard_results:
            remediation = result.remediation or "—"
            lines.append(
                f"| {result.name} | {result.status.value.upper()} | {result.details} | {remediation} |"
            )
    lines.append("")

    lines.append("## Roadmap Alignment")
    if phases is None:
        lines.append("_Roadmap section skipped by request_.")
    elif not phases:
        lines.append("")
        lines.append("No roadmap entries matched the requested keyword.")
    else:
        for phase in phases:
            lines.append("")
            lines.append(f"### {phase.identifier} — {phase.title}")
            for section, entries in phase.sections.items():
                lines.append("")
                lines.append(f"#### {section}")
                for entry in entries:
                    lines.append(f"- {entry}")
    return "\n".join(lines).rstrip()


def format_json(scorecard_results: ScorecardResults, phases: RoadmapPhases) -> str:
    if scorecard_results is None:
        scorecard_payload = None
    else:
        scorecard_payload = json.loads(environment_scorecard.format_json(scorecard_results))

    if phases is None:
        roadmap_payload = None
    else:
        roadmap_payload = json.loads(environment_roadmap.format_json(phases))

    payload = {
        "scorecard": scorecard_payload,
        "roadmap": roadmap_payload,
    }
    return json.dumps(payload, indent=2)


def render(scorecard_results: ScorecardResults, phases: RoadmapPhases, output_format: str) -> str:
    if output_format == "markdown":
        return format_markdown(scorecard_results, phases)
    if output_format == "json":
        return format_json(scorecard_results, phases)
    return format_text(scorecard_results, phases)


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
    try:
        scorecard_results = collect_scorecard_results(args)
        phases = collect_roadmap_phases(args)
        output = render(scorecard_results, phases, args.format)
    except Exception as exc:  # pragma: no cover - CLI utility
        print(f"Error: {exc}")
        sys.exit(1)
    else:
        emit_output(output, args.output)


if __name__ == "__main__":
    main()
