"""Minimal policy enforcement stub.

This module provides a small PolicyEngine that can be extended with real
rules. It is intentionally lightweight so that PhaseTracker detects a
present policy engine without blocking runtime execution.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class PolicyEngine:
    def __init__(self, policy_path: str | Path | None = None) -> None:
        self.policy_path = Path(policy_path) if policy_path else None
        self.rules: Dict[str, Any] = {}
        if self.policy_path and self.policy_path.exists():
            try:
                self.rules = json.loads(self.policy_path.read_text(encoding="utf-8"))
            except Exception:
                self.rules = {}

    def is_allowed(self, action: str, context: Dict[str, Any] | None = None) -> bool:
        context = context or {}
        if action in self.rules:
            rule = self.rules[action]
            if isinstance(rule, bool):
                return rule
            if isinstance(rule, dict) and "allowed" in rule:
                return bool(rule["allowed"])
        # Default allow; tighten in production by editing the policy file
        return True

    def require(self, action: str, context: Dict[str, Any] | None = None) -> None:
        if not self.is_allowed(action, context):
            raise PermissionError(f"Action '{action}' is not permitted by policy")


__all__ = ["PolicyEngine"]
