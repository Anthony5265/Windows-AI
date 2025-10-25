"""Environment orchestration for installer plugins and tools.

This module builds on :mod:`installer.env` and :mod:`installer.plugins` to
create isolated virtual or conda environments for each plugin (or tool
category).  Prior to installation it performs a light-weight analysis of the
requested package versions to warn about obvious conflicts.  When possible the
conflicts can be automatically resolved by selecting the highest pinned version.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Iterable, Tuple, Dict, List, Set

from packaging.requirements import Requirement
from packaging.version import Version
from packaging.specifiers import SpecifierSet

from installer import env, plugins
from updater import Updater


@dataclass
class ParsedRequirement:
    extras: Set[str]
    specifier: SpecifierSet
    marker: str | None
    original: str


def _parse_requirements(requirements: Iterable[str]) -> Dict[str, List[ParsedRequirement]]:
    """Group requirement strings by normalized package name, preserving extras and markers."""

    grouped: Dict[str, List[ParsedRequirement]] = {}
    for req_str in requirements:
        req = Requirement(req_str)
        name = req.name.lower()
        grouped.setdefault(name, []).append(
            ParsedRequirement(set(req.extras), req.specifier, str(req.marker) if req.marker else None, req_str)
        )
    return grouped


def _merge_markers(markers: Iterable[str | None]) -> str | None:
    markers = list(markers)
    if any(m is None for m in markers):
        return None
    unique = sorted({m for m in markers if m})
    if not unique:
        return None
    if len(unique) == 1:
        return unique[0]
    return " or ".join(f"({m})" if " or " in m or " and " in m else m for m in unique)


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
        extras = set().union(*(r.extras for r in reqs))
        extras_str = f"[{','.join(sorted(extras))}]" if extras else ""

        pinned = {spec.version for r in reqs for spec in r.specifier if spec.operator in {"==", "==="}}
        if len(pinned) > 1:
            conflicts[name] = [r.original for r in reqs]
            if auto_resolve:
                chosen = max(pinned, key=Version)
                marker = _merge_markers(r.marker for r in reqs)
                req_str = f"{name}{extras_str}=={chosen}"
                if marker:
                    req_str += f"; {marker}"
                resolved.append(req_str)
            continue

        spec: SpecifierSet | None = None
        for r in reqs:
            spec = r.specifier if spec is None else spec & r.specifier
        spec_str = str(spec) if spec and str(spec) else ""
        marker = _merge_markers(r.marker for r in reqs)
        req_str = f"{name}{extras_str}{spec_str}"
        if marker:
            req_str += f"; {marker}"
        resolved.append(req_str)

    return resolved, conflicts


def setup_all(
    search_path: str | Path | None = None,
    auto_resolve: bool = True,
    update: bool = False,
    updater_kwargs: Dict[str, object] | None = None,
) -> Dict[str, Dict[str, object]]:
    """Discover plugins and install their dependencies in isolated envs.

    Parameters
    ----------
    search_path:
        Optional directory to search for plugin modules.  This mirrors the
        parameter of :func:`installer.plugins.discover_plugins` and mainly exists
        to facilitate unit testing.
    auto_resolve:
        Passed to :func:`resolve_conflicts`.
    update:
        When ``True`` the application is updated using :class:`updater.Updater`
        before environments are created.
    updater_kwargs:
        Optional keyword arguments passed to :class:`updater.Updater` when
        ``update`` is ``True``.

    Returns
    -------
    dict
        Mapping of plugin name to information about the created environment. Each
        entry contains the environment path, installed packages and any
        conflicts encountered.
    """

    if update:
        Updater(**(updater_kwargs or {})).update()

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
