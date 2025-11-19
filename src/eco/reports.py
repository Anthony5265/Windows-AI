"""Simple eco report generation and tips."""

from __future__ import annotations

from typing import List

from .tracker import EnergyTracker

_TIPS = [
    "Dim your display to reduce power usage.",
    "Close applications you are not actively using.",
    "Schedule heavy compute for off‑peak hours.",
]


def eco_tips() -> List[str]:
    """Return a list of energy saving tips."""

    return list(_TIPS)


def generate_report() -> str:
    """Generate a small human readable eco report."""

    tracker = EnergyTracker()
    info = tracker.current()
    lines = ["# Eco Report"]
    lines.append(f"Battery: {info.percent if info.percent is not None else 'n/a'}%")
    lines.append(
        f"Plugged in: {'yes' if info.power_plugged else 'no' if info.power_plugged is not None else 'n/a'}"
    )
    lines.append("")
    lines.append("## Tips")
    for tip in eco_tips():
        lines.append(f"- {tip}")
    return "\n".join(lines)
