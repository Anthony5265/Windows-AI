#!/usr/bin/env python3
"""Map roadmap milestones to environment provisioning commitments."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List


PHASE_HEADER = re.compile(r"^##\s+(Phase\s+\d+):\s*(.+)$")
SUBHEADING = re.compile(r"^###\s+(.+?)(:)?$")
LIST_ITEM = re.compile(r"^(?:[\*-]|\d+\.)\s+")


@dataclass
class PhaseAlignment:
    """Environment-related roadmap details captured for a single phase."""

    identifier: str
    title: str
    sections: Dict[str, List[str]] = field(default_factory=dict)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Align roadmap phases with environment provisioning requirements."
        )
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
        help=(
            "Keyword to filter roadmap items. Use to explore adjacent focus areas"
            " (default: environment)."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the rendered report instead of stdout.",
    )
    return parser.parse_args()


def normalize_list_item(text: str) -> str:
    text = text.lstrip()
    text = re.sub(r"^(?:[\*-]|\d+\.)\s+", "", text)
    return text.strip()


def add_entry(phase: PhaseAlignment, section: str, entry: str) -> None:
    phase.sections.setdefault(section, []).append(entry.strip())


def parse_roadmap(path: Path, keyword: str) -> List[PhaseAlignment]:
    if not path.exists():
        raise FileNotFoundError(f"Roadmap file not found: {path}")

    phases: List[PhaseAlignment] = []
    phase: PhaseAlignment | None = None
    current_section: str | None = None
    pending_item: str | None = None
    pending_section: str | None = None
    keyword_lower = keyword.lower()

    def flush_pending() -> None:
        nonlocal pending_item, pending_section
        if pending_item is None or phase is None:
            return
        if keyword_lower in pending_item.lower():
            target = pending_section or current_section or "Highlights"
            add_entry(phase, target, pending_item)
        pending_item = None
        pending_section = None

    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            stripped = line.strip()

            header_match = PHASE_HEADER.match(stripped)
            if header_match:
                flush_pending()
                if phase and any(phase.sections.values()):
                    phases.append(phase)
                phase = PhaseAlignment(
                    identifier=header_match.group(1),
                    title=header_match.group(2),
                )
                current_section = None
                continue

            if phase is None:
                continue

            subheading_match = SUBHEADING.match(stripped)
            if subheading_match:
                flush_pending()
                current_section = subheading_match.group(1).strip()
                continue

            if not stripped:
                flush_pending()
                continue

            if LIST_ITEM.match(stripped):
                flush_pending()
                pending_item = normalize_list_item(stripped)
                pending_section = current_section or "Highlights"
                continue

            if pending_item is not None and line.startswith((" ", "\t")):
                pending_item += " " + stripped
                continue

            flush_pending()

            if keyword_lower in stripped.lower():
                target_section = current_section or "Context"
                add_entry(phase, target_section, stripped)

    if phase:
        flush_pending()
        if any(phase.sections.values()):
            phases.append(phase)

    return phases


def format_text(phases: Iterable[PhaseAlignment]) -> str:
    phases = list(phases)
    total_items = sum(len(items) for phase in phases for items in phase.sections.values())
    lines = [
        "Environment Roadmap Alignment",
        "===============================",
        (
            "Summary: "
            f"{total_items} environment-focused entries across {len(phases)} phase(s)."
        ),
        "",
    ]

    if not phases:
        lines.append("No roadmap entries matched the requested keyword.")
        return "\n".join(lines)

    for phase in phases:
        header = f"{phase.identifier} — {phase.title}"
        lines.append(header)
        lines.append("-" * len(header))
        for section, entries in phase.sections.items():
            lines.append(f"  {section}:")
            for entry in entries:
                lines.append(f"    - {entry}")
        lines.append("")

    return "\n".join(lines).rstrip()


def format_markdown(phases: Iterable[PhaseAlignment]) -> str:
    phases = list(phases)
    total_items = sum(len(items) for phase in phases for items in phase.sections.values())
    lines = ["# Environment Roadmap Alignment", ""]
    lines.append(
        f"**Summary:** {total_items} environment-focused entries across {len(phases)} phase(s)."
    )
    lines.append("")

    if not phases:
        lines.append("No roadmap entries matched the requested keyword.")
        return "\n".join(lines)

    for phase in phases:
        lines.append(f"## {phase.identifier} — {phase.title}")
        lines.append("")
        for section, entries in phase.sections.items():
            lines.append(f"### {section}")
            for entry in entries:
                lines.append(f"- {entry}")
            lines.append("")
    return "\n".join(lines).rstrip()


def format_json(phases: Iterable[PhaseAlignment]) -> str:
    payload = [
        {
            "phase": phase.identifier,
            "title": phase.title,
            "sections": dict(phase.sections),
        }
        for phase in phases
    ]
    return json.dumps(payload, indent=2)


def render(phases: Iterable[PhaseAlignment], output_format: str) -> str:
    if output_format == "markdown":
        return format_markdown(phases)
    if output_format == "json":
        return format_json(phases)
    return format_text(phases)


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
    phases = parse_roadmap(args.roadmap, args.keyword)
    output = render(phases, args.format)
    emit_output(output, args.output)


if __name__ == "__main__":
    main()
