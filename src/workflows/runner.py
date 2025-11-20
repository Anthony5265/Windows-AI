from __future__ import annotations

import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from terminal.engine import TerminalEngine

from .catalog import WorkflowCatalog
from .models import WorkflowSpec


@dataclass
class WorkflowRunLog:
    """Record of an executed workflow."""

    id: str
    mode: str
    inputs: Dict[str, Any]
    result: Any
    duration: float
    exit_code: int


class WorkflowRunner:
    """Execute workflows from a :class:`WorkflowCatalog`."""

    def __init__(
        self,
        catalog: WorkflowCatalog,
        *,
        terminal: Optional[TerminalEngine] = None,
    ) -> None:
        self.catalog = catalog
        self.terminal = terminal or TerminalEngine()
        self.logs: list[WorkflowRunLog] = []

    # ------------------------------------------------------------------ helpers
    def _record(self, spec: WorkflowSpec, inputs: Dict[str, Any], result: Any, duration: float, exit_code: int) -> WorkflowRunLog:
        log = WorkflowRunLog(
            id=spec.id,
            mode=spec.run.mode,
            inputs=dict(inputs),
            result=result,
            duration=duration,
            exit_code=exit_code,
        )
        self.logs.append(log)
        return log

    # -------------------------------------------------------------------- public
    def run(self, workflow_id: str, overrides: Optional[Dict[str, Any]] = None) -> WorkflowRunLog:
        spec = self.catalog.get(workflow_id)
        if spec is None:
            raise KeyError(f"Workflow not found: {workflow_id}")

        inputs = self.catalog.apply_inputs(spec, overrides)
        start = time.monotonic()
        result: Any = None
        exit_code = 0

        try:
            if spec.run.mode == "shell":
                result = self._run_shell(spec, inputs)
            elif spec.run.mode == "script":
                result = self._run_script(spec, inputs)
            elif spec.run.mode == "action":
                result = self._run_action(spec, inputs)
            else:
                raise ValueError(f"Unsupported workflow mode: {spec.run.mode}")
        except subprocess.CalledProcessError as exc:
            exit_code = exc.returncode
            result = exc.stderr or str(exc)
        except Exception as exc:  # pragma: no cover - catch for logging
            exit_code = -1
            result = str(exc)
        finally:
            duration = time.monotonic() - start

        return self._record(spec, inputs, result, duration, exit_code)

    # ----------------------------------------------------------------- execution
    def _run_shell(self, spec: WorkflowSpec, inputs: Dict[str, Any]) -> str:
        command = self.catalog.render_command(spec, inputs)
        if not command:
            raise ValueError("Shell workflow missing command")
        return self.terminal.run(command)

    def _run_script(self, spec: WorkflowSpec, inputs: Dict[str, Any]) -> str:
        script = self.catalog.render_script(spec, inputs)
        if not script:
            raise ValueError("Script workflow missing script content")
        language = spec.run.script_language.lower()
        if language not in {"python", "powershell", "shell"}:
            raise ValueError(f"Unsupported script language: {language}")

        if language == "python":
            return self._execute_python_script(script)
        if language == "powershell":
            return self._execute_shell_script(script, executable="pwsh")
        return self._execute_shell_script(script)

    def _run_action(self, spec: WorkflowSpec, inputs: Dict[str, Any]) -> Dict[str, Any]:
        action_name = spec.run.action
        if not action_name:
            raise ValueError("Action workflow missing action name")
        params = self.catalog.render_action_params(spec, inputs)
        if action_name == "shell":
            command = params.get("command")
            if not command:
                raise ValueError("Action 'shell' requires command parameter")
            try:
                output = self.terminal.run(command)
            except ValueError:
                output = self._run_subprocess(command)
            return {"stdout": output}
        if action_name == "start_process":
            exe = params.get("exe")
            if not exe:
                raise ValueError("Action 'start_process' requires exe parameter")
            args = params.get("args", [])
            self._spawn_process(exe, args)
            return {"started": True, "exe": exe, "args": args}
        return {"action": action_name, "params": params}

    # ------------------------------------------------------------ script helpers
    def _execute_python_script(self, script: str) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as handle:
            handle.write(script)
            path = Path(handle.name)
        try:
            completed = subprocess.run(
                ["python", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
        finally:
            path.unlink(missing_ok=True)
        return completed.stdout.strip()

    def _execute_shell_script(self, script: str, executable: str | None = None) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as handle:
            handle.write(script)
            path = Path(handle.name)
        try:
            cmd = [executable or "sh", str(path)] if executable else ["sh", str(path)]
            completed = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
            )
        finally:
            path.unlink(missing_ok=True)
        return completed.stdout.strip()

    def _spawn_process(self, exe: str, args: Any) -> None:
        if isinstance(args, str):
            args = [args]
        subprocess.Popen([exe, *args])

    def _run_subprocess(self, command: str) -> str:
        completed = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
        )
        return completed.stdout.strip()
