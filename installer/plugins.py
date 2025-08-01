"""Plugin registry and discovery for the installer."""
from __future__ import annotations

from dataclasses import dataclass, field
from importlib.metadata import entry_points
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any


@dataclass
class PluginRegistry:
    """Collects contributions from installer plugins.

    Plugins can request extra dependencies or register UI components.  The
    registry stores requested packages keyed by plugin so the installer can
    create isolated environments per plugin.
    """

    dependencies: dict[str, set[str]] = field(default_factory=dict)
    ui_components: dict[str, Any] = field(default_factory=dict)
    _current_plugin: str | None = field(default=None, init=False, repr=False)

    def add_dependency(self, requirement: str) -> None:
        """Request installation of an additional package."""

        plugin = self._current_plugin or "global"
        self.dependencies.setdefault(plugin, set()).add(requirement)

    def register_ui_component(self, name: str, component: Any) -> None:
        """Register a UI component provided by a plugin."""

        self.ui_components[name] = component


def _apply_plugin(plugin: Any, registry: PluginRegistry, name: str) -> None:
    """Invoke a plugin object, module, or factory with the registry."""

    registry._current_plugin = name
    try:
        if hasattr(plugin, "register") and callable(plugin.register):
            plugin.register(registry)
        elif callable(plugin):
            plugin(registry)
        else:
            raise TypeError("Plugin must be callable or expose a register() function")
    finally:
        registry._current_plugin = None


def _load_module(path: Path) -> ModuleType:
    spec = spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load plugin module from {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def discover_plugins(search_path: str | Path | None = None) -> PluginRegistry:
    """Discover plugins via entry points and an optional directory.

    Parameters
    ----------
    search_path:
        Directory containing plugin modules.  Each ``.py`` file will be imported
        and expected to expose a ``register(registry)`` function.  Files starting
        with ``_`` are ignored.
    """

    registry = PluginRegistry()

    # Entry points
    for ep in entry_points().select(group="installer_plugins"):
        plugin = ep.load()
        _apply_plugin(plugin, registry, ep.name)

    # Search directory
    if search_path is not None:
        path = Path(search_path)
        for file in path.glob("*.py"):
            if file.name.startswith("_"):
                continue
            module = _load_module(file)
            _apply_plugin(module, registry, file.stem)

    return registry


__all__ = ["PluginRegistry", "discover_plugins"]
