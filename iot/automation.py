from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

import yaml

from terminal.engine import TerminalEngine


class WorkflowAutomation:
    """Map device events to terminal workflows."""

    def __init__(self, workflow_dir: str | Path = "assets/terminal/workflows") -> None:
        self.workflow_dir = Path(workflow_dir)
        self._bindings: Dict[Tuple[str, str], str] = {}

    def register(self, device_id: str, event: str, workflow_id: str) -> None:
        """Bind a device event to a workflow ID."""
        self._bindings[(device_id, event)] = workflow_id

    def emit(self, device_id: str, event: str) -> None:
        """Trigger the workflow bound to *device_id*/*event*, if any."""
        workflow_id = self._bindings.get((device_id, event))
        if not workflow_id:
            return
        self._run_workflow(workflow_id)

    def _run_workflow(self, workflow_id: str) -> None:
        wf_file = self.workflow_dir / f"{workflow_id}.yml"
        if not wf_file.exists():
            raise FileNotFoundError(wf_file)
        data = yaml.safe_load(wf_file.read_text())
        run = data.get("run", {})
        if run.get("mode") == "action":
            action = run.get("action", {})
            if action.get("name") == "shell":
                command = action.get("params", {}).get("command")
                if command:
                    engine = TerminalEngine()
                    engine.run(command)
