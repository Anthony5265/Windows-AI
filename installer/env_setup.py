"""Environment orchestration for installer plugins and tools.

This module builds on :mod:`installer.env` and :mod:`installer.plugins` to
create isolated virtual or conda environments for each plugin (or tool
category).  Prior to installation it performs a light-weight analysis of the
requested package versions to warn about obvious conflicts.  When possible the
conflicts can be automatically resolved by selecting the highest pinned version.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple, Dict, List

from packaging.requirements import Requirement
from packaging.version import Version
from packaging.specifiers import SpecifierSet

from . import env, plugins


def _parse_requirements(requirements: Iterable[str]) -> Dict[str, List[Requirement]]:
    """Group requirement strings by normalized package name."""

    grouped: Dict[str, List[Requirement]] = {}
    for req_str in requirements:
        req = Requirement(req_str)
        name = req.name.lower()
        grouped.setdefault(name, []).append(req)
    return grouped


def resolve_conflicts(requirements: Iterable[str], auto_resolve: bool = True) -> Tuple[List[str], Dict[str, List[str]]]:
    """Return a list of resolved requirement strings and detected conflicts.

    Parameters
    ----------
    requirements:
        Iterable of requirement strings.
    auto_resolve:
        When ``True`` conflicting pinned versions are resolved by choosing the
        highest version.  When ``False`` the conflict remains and no package is
        suggested for installation.
    """

    grouped = _parse_requirements(requirements)
    resolved: List[str] = []
    conflicts: Dict[str, List[str]] = {}

    for name, reqs in grouped.items():
        if len(reqs) == 1:
            resolved.append(str(reqs[0]))
            continue

        pinned = {spec.version for r in reqs for spec in r.specifier if spec.operator in {"==", "==="}}
        if len(pinned) > 1:
            # conflicting explicit versions
            conflicts[name] = [str(r) for r in reqs]
            if auto_resolve:
                chosen = max(pinned, key=Version)
                resolved.append(f"{name}=={chosen}")
            continue

        # combine remaining specifiers (if any)
        spec: SpecifierSet | None = None
        for r in reqs:
            spec = r.specifier if spec is None else spec & r.specifier
        resolved.append(f"{name}{spec}")

    return resolved, conflicts


def setup_all(search_path: str | Path | None = None, auto_resolve: bool = True) -> Dict[str, Dict[str, object]]:
    """Discover plugins and install their dependencies in isolated envs.

    Parameters
    ----------
    search_path:
        Optional directory to search for plugin modules.  This mirrors the
        parameter of :func:`installer.plugins.discover_plugins` and mainly exists
        to facilitate unit testing.
    auto_resolve:
        Passed to :func:`resolve_conflicts`.

    Returns
    -------
    dict
        Mapping of plugin name to information about the created environment. Each
        entry contains the environment path, installed packages and any
        conflicts encountered.
    """

    registry = plugins.discover_plugins(search_path)
    report: Dict[str, Dict[str, object]] = {}

    for name, deps in sorted(registry.dependencies.items()):
        packages, conflicts = resolve_conflicts(deps, auto_resolve=auto_resolve)
        env_path = env.create_env(name)
        env.install_packages(env_path, packages)
        report[name] = {
            "env_path": env_path,
            "packages": packages,
            "conflicts": conflicts,
        }
    return report


__all__ = ["resolve_conflicts", "setup_all"]
