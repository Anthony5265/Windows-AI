from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

import yaml

WORKFLOW_DIR = Path(__file__).resolve().parents[1] / "assets" / "terminal" / "workflows"


@dataclass
class Step:
    id: str
    name: str
    next: List[str] = field(default_factory=list)


@dataclass
class Workflow:
    steps: Dict[str, Step] = field(default_factory=dict)


def save_workflow(workflow: Workflow, path: Path) -> None:
    data = {
        "steps": {
            sid: {"name": step.name, "next": step.next}
            for sid, step in workflow.steps.items()
        }
    }
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh)


def load_workflow(path: Path) -> Workflow:
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    steps: Dict[str, Step] = {}
    for sid, info in (data.get("steps") or {}).items():
        steps[sid] = Step(id=sid, name=info.get("name", ""), next=list(info.get("next") or []))
    return Workflow(steps=steps)


__all__ = ["Step", "Workflow", "save_workflow", "load_workflow", "WORKFLOW_DIR"]
