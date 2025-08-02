"""Model backend selection utilities."""

from __future__ import annotations

from typing import Any, Dict

from . import system_info


def select_backend(task: str, specs: Dict[str, Any]) -> str:
    """Choose between a local model and a remote API for ``task``.

    Parameters
    ----------
    task:
        Identifier for the task requesting a model backend.  Currently unused
        but reserved for future heuristics.
    specs:
        Hardware requirements for running the task locally.  Recognised keys are
        ``requires_gpu`` (bool), ``min_vram_gb`` (float) and ``min_ram_gb``
        (float).  Missing keys are treated as no requirement.

    Returns
    -------
    str
        ``"local"`` if the system appears to meet the requirements, otherwise
        ``"remote"``.
    """

    info = system_info.detect_system()

    def meets(value: float | None, requirement: float | None) -> bool:
        if requirement is None:
            return True
        if value is None:
            return False
        return value >= requirement

    if specs.get("requires_gpu") and not info.get("gpu_name"):
        return "remote"

    if not meets(info.get("gpu_vram_gb"), specs.get("min_vram_gb")):
        return "remote"

    if not meets(info.get("ram_total_gb"), specs.get("min_ram_gb")):
        return "remote"

    return "local"
