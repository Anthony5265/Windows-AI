"""Basic threat monitoring using heuristic checks.

In a real deployment this module could leverage an external LLM service to
assess logs or user activity.  For the purposes of the tests we implement a
lightweight keyword based detector that mimics an LLM driven system.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass
class ThreatMonitor:
    """Simple heuristic threat detector."""

    keywords: Iterable[str] = field(
        default_factory=lambda: ["attack", "exploit", "malware", "phishing"]
    )

    def analyze(self, text: str) -> List[str]:
        """Return a list of suspicious keywords found in ``text``."""

        hits = [kw for kw in self.keywords if re.search(rf"\b{re.escape(kw)}\b", text, re.I)]
        return hits
