from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import re

import yaml

from .models import WorkflowInput, WorkflowRunDefinition, WorkflowSpec

_TEMPLATE_PATTERN = re.compile(r"\$\{\{\s*([a-zA-Z_][\w-]*)\s*\}\}")


@dataclass
class CatalogEntry:
    spec: WorkflowSpec
    score: float = 0.0


class WorkflowCatalog:
    """Load workflow YAML files and provide fuzzy search."""

    def __init__(self, root: str | Path = "assets/terminal/workflows") -> None:
        self.root = Path(root)
        self._workflows: Dict[str, WorkflowSpec] = {}
        self.reload()

    # ------------------------------------------------------------------ loading
    def reload(self) -> None:
        self._workflows.clear()
        if not self.root.exists():
            return
        for path in sorted(self.root.rglob("*.yml")):
            spec = self._parse_file(path)
            if spec:
                self._workflows[spec.id] = spec

    def _parse_file(self, path: Path) -> Optional[WorkflowSpec]:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}

        workflow_id = data.get("id") or path.stem
        title = data.get("title", workflow_id)
        description = data.get("description", "")
        tags = list(data.get("tags") or [])
        inputs = [
            WorkflowInput(
                name=item.get("name", ""),
                type=item.get("type", "string"),
                description=item.get("description"),
                default=item.get("default"),
            )
            for item in (data.get("inputs") or [])
        ]
        run_section = data.get("run") or {}
        mode = (run_section.get("mode") or "shell").lower()
        script_block = None
        script_language = "python"
        script_section = run_section.get("script")
        if isinstance(script_section, str):
            script_block = script_section
        elif isinstance(script_section, dict):
            script_block = script_section.get("content")
            script_language = script_section.get("language", script_language)
        action_name = None
        action_params = {}
        if isinstance(run_section.get("action"), dict):
            action_name = run_section["action"].get("name")
            action_params = run_section["action"].get("params", {})

        run = WorkflowRunDefinition(
            mode=mode,
            command=run_section.get("command"),
            script=script_block,
            script_language=script_language,
            action=action_name,
            action_params=action_params,
        )

        spec = WorkflowSpec(
            id=workflow_id,
            title=title,
            description=description,
            tags=tags,
            inputs=inputs,
            run=run,
            path=str(path),
        )
        return spec

    # ------------------------------------------------------------------ public
    def list(self) -> List[WorkflowSpec]:
        return list(self._workflows.values())

    def get(self, workflow_id: str) -> Optional[WorkflowSpec]:
        return self._workflows.get(workflow_id)

    # ------------------------------------------------------------------ search
    def search(self, query: str, limit: int = 5) -> List[WorkflowSpec]:
        if not query:
            return sorted(self._workflows.values(), key=lambda s: s.display_name())[:limit]
        scored: List[CatalogEntry] = []
        for spec in self._workflows.values():
            haystack = " ".join([spec.id, spec.title, " ".join(spec.tags)]).lower()
            score = self._fuzzy_score(query.lower(), haystack)
            if score > 0:
                scored.append(CatalogEntry(spec=spec, score=score))
        scored.sort(key=lambda entry: (-entry.score, entry.spec.display_name()))
        return [entry.spec for entry in scored[:limit]]

    @staticmethod
    def _fuzzy_score(query: str, haystack: str) -> float:
        if query in haystack:
            return len(query) / len(haystack)
        # fallback ratio based on containment of characters in order
        pos = -1
        matches = 0
        for ch in query:
            pos = haystack.find(ch, pos + 1)
            if pos == -1:
                return 0.0
            matches += 1
        return matches / max(len(haystack), 1)

    # ------------------------------------------------------------ templating
    def render(self, text: str, values: Dict[str, object]) -> str:
        def _replace(match: re.Match[str]) -> str:
            key = match.group(1)
            return str(values.get(key, match.group(0)))

        return _TEMPLATE_PATTERN.sub(_replace, text)

    def apply_inputs(self, spec: WorkflowSpec, overrides: Optional[Dict[str, object]] = None) -> Dict[str, object]:
        resolved: Dict[str, object] = {}
        overrides = overrides or {}
        for item in spec.inputs:
            if item.name in overrides:
                resolved[item.name] = overrides[item.name]
            elif item.default is not None:
                resolved[item.name] = item.default
        for key, value in overrides.items():
            if key not in resolved:
                resolved[key] = value
        return resolved

    def render_command(self, spec: WorkflowSpec, inputs: Dict[str, object]) -> Optional[str]:
        command = spec.run.command
        if not command:
            return None
        return self.render(command, inputs)

    def render_script(self, spec: WorkflowSpec, inputs: Dict[str, object]) -> Optional[str]:
        script = spec.run.script
        if not script:
            return None
        return self.render(script, inputs)

    def render_action_params(self, spec: WorkflowSpec, inputs: Dict[str, object]) -> Dict[str, object]:
        params: Dict[str, object] = {}
        for key, value in spec.run.action_params.items():
            if isinstance(value, str):
                params[key] = self.render(value, inputs)
            else:
                params[key] = value
        return params


__all__ = ["WorkflowCatalog"]
