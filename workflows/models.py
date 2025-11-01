from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowInput:
    """Describe a parameter requested by a workflow."""

    name: str
    type: str = "string"
    description: Optional[str] = None
    default: Optional[Any] = None


@dataclass
class WorkflowRunDefinition:
    """Execution details loaded from the workflow specification."""

    mode: str
    command: Optional[str] = None
    script: Optional[str] = None
    script_language: str = "python"
    action: Optional[str] = None
    action_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowSpec:
    """A parsed workflow specification."""

    id: str
    title: str
    description: str
    tags: List[str]
    inputs: List[WorkflowInput]
    run: WorkflowRunDefinition
    path: Optional[str] = None

    def display_name(self) -> str:
        return self.title or self.id
