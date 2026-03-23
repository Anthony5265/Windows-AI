"""Plugin Dependency Resolver for Windows AI.

Resolves inter-plugin dependency graphs and determines safe load order.
Detects circular dependencies and missing requirements.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    """Raised when dependency resolution fails."""


class CircularDependencyError(DependencyError):
    """Raised when a circular dependency is detected."""


class MissingDependencyError(DependencyError):
    """Raised when a required dependency is not available."""


class PluginDependencyResolver:
    """Resolve plugin dependencies and compute safe load order.

    Usage
    -----
    >>> resolver = PluginDependencyResolver()
    >>> resolver.register("audio-speech", depends_on=["ai-providers"])
    >>> resolver.register("ai-providers", depends_on=[])
    >>> order = resolver.resolve()
    >>> order
    ['ai-providers', 'audio-speech']
    """

    def __init__(self) -> None:
        self._plugins: Dict[str, Dict[str, Any]] = {}
        self._dependencies: Dict[str, List[str]] = defaultdict(list)
        self._reverse_deps: Dict[str, List[str]] = defaultdict(list)

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        plugin_id: str,
        *,
        depends_on: Optional[List[str]] = None,
        version: str = "0.0.0",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a plugin and its dependencies."""
        deps = depends_on or []
        self._plugins[plugin_id] = {
            "version": version,
            "depends_on": deps,
            "metadata": metadata or {},
        }
        self._dependencies[plugin_id] = deps
        for dep in deps:
            self._reverse_deps[dep].append(plugin_id)

    def unregister(self, plugin_id: str) -> bool:
        """Remove a plugin from the resolver. Returns True if found."""
        if plugin_id not in self._plugins:
            return False
        deps = self._dependencies.pop(plugin_id, [])
        for dep in deps:
            if plugin_id in self._reverse_deps.get(dep, []):
                self._reverse_deps[dep].remove(plugin_id)
        self._plugins.pop(plugin_id, None)
        return True

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(self, *, ignore_missing: bool = False) -> List[str]:
        """Compute a topological load order for all registered plugins.

        Raises
        ------
        CircularDependencyError
            If the dependency graph contains cycles.
        MissingDependencyError
            If a required dependency is not registered (unless *ignore_missing*).
        """
        # Validate all dependencies exist
        if not ignore_missing:
            for pid, deps in self._dependencies.items():
                for dep in deps:
                    if dep not in self._plugins:
                        raise MissingDependencyError(
                            f"Plugin '{pid}' requires '{dep}' which is not registered"
                        )

        return self._topological_sort()

    def resolve_for(self, plugin_id: str) -> List[str]:
        """Return the ordered list of dependencies for a single plugin.

        The list includes transitive dependencies and ends with *plugin_id*.
        """
        if plugin_id not in self._plugins:
            raise DependencyError(f"Plugin not registered: {plugin_id}")

        visited: Set[str] = set()
        order: List[str] = []
        path: Set[str] = set()

        def dfs(pid: str) -> None:
            if pid in path:
                raise CircularDependencyError(
                    f"Circular dependency detected involving '{pid}'"
                )
            if pid in visited:
                return
            path.add(pid)
            for dep in self._dependencies.get(pid, []):
                if dep in self._plugins:
                    dfs(dep)
            path.discard(pid)
            visited.add(pid)
            order.append(pid)

        dfs(plugin_id)
        return order

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_dependents(self, plugin_id: str) -> List[str]:
        """Return plugins that depend on *plugin_id*."""
        return list(self._reverse_deps.get(plugin_id, []))

    def get_dependencies(self, plugin_id: str) -> List[str]:
        """Return direct dependencies of *plugin_id*."""
        return list(self._dependencies.get(plugin_id, []))

    def is_safe_to_remove(self, plugin_id: str) -> Tuple[bool, List[str]]:
        """Check if *plugin_id* can be safely removed.

        Returns ``(True, [])`` if no other plugin depends on it,
        otherwise ``(False, [list_of_dependents])``.
        """
        dependents = self.get_dependents(plugin_id)
        return (len(dependents) == 0, dependents)

    def find_circular_dependencies(self) -> List[List[str]]:
        """Return all circular dependency chains (if any)."""
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(pid: str) -> None:
            visited.add(pid)
            rec_stack.add(pid)
            path.append(pid)

            for dep in self._dependencies.get(pid, []):
                if dep not in self._plugins:
                    continue
                if dep not in visited:
                    dfs(dep)
                elif dep in rec_stack:
                    idx = path.index(dep)
                    cycles.append(path[idx:] + [dep])

            path.pop()
            rec_stack.discard(pid)

        for pid in self._plugins:
            if pid not in visited:
                dfs(pid)

        return cycles

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _topological_sort(self) -> List[str]:
        """Kahn's algorithm for topological sorting."""
        in_degree: Dict[str, int] = defaultdict(int)
        for pid in self._plugins:
            in_degree.setdefault(pid, 0)
            for dep in self._dependencies.get(pid, []):
                if dep in self._plugins:
                    in_degree[pid] += 1

        queue: deque[str] = deque(
            pid for pid, deg in in_degree.items() if deg == 0
        )
        order: List[str] = []

        while queue:
            pid = queue.popleft()
            order.append(pid)
            for dependent in self._reverse_deps.get(pid, []):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        if len(order) != len(self._plugins):
            remaining = set(self._plugins) - set(order)
            raise CircularDependencyError(
                f"Circular dependency among: {', '.join(sorted(remaining))}"
            )

        return order

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """Return resolver statistics."""
        return {
            "total_plugins": len(self._plugins),
            "total_dependencies": sum(
                len(deps) for deps in self._dependencies.values()
            ),
            "plugins_with_no_deps": sum(
                1 for deps in self._dependencies.values() if not deps
            ),
            "most_depended_on": self._most_depended_on(5),
        }

    def _most_depended_on(self, n: int) -> List[Dict[str, Any]]:
        counts = {
            pid: len(self._reverse_deps.get(pid, []))
            for pid in self._plugins
        }
        top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:n]
        return [{"plugin_id": pid, "dependents": cnt} for pid, cnt in top]
