"""Policy management helpers based on ADMX templates."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import xml.etree.ElementTree as ET

__all__ = ["PolicyTemplate", "PolicyManager"]


@dataclass
class PolicyTemplate:
    """Simple representation of an ADMX policy template."""

    name: str
    settings: Dict[str, Any] = field(default_factory=dict)


class PolicyManager:
    """Load and query policy templates."""

    def __init__(self) -> None:
        self.templates: Dict[str, PolicyTemplate] = {}

    def load_template(self, path: str | Path) -> None:
        """Load an ADMX XML template from ``path``."""

        tree = ET.parse(path)
        root = tree.getroot()
        name = root.attrib.get("name", Path(path).stem)
        policies = {
            node.attrib.get("name", ""): node.attrib
            for node in root.findall(".//policy")
        }
        self.templates[name] = PolicyTemplate(name, policies)

    def get(self, name: str) -> Optional[PolicyTemplate]:
        """Return a previously loaded template."""

        return self.templates.get(name)
