# Installer Plugin System

The installer can be extended through a lightweight plugin mechanism. Plugins
can request additional dependencies or register UI components that will be
exposed by the installer.

## Discovery

Plugins are discovered in two ways:

1. **Entry points** – any installed package that defines an
   `installer_plugins` entry point will be loaded.
2. **Directory scanning** – pass a directory to
   `discover_plugins()` and each `.py` file in that directory will be imported.
   Files beginning with `_` are ignored.

## Writing a Plugin

A plugin is simply a callable that accepts a `PluginRegistry` instance. Most
modules expose a `register(registry)` function.  Dependencies are recorded per
plugin so the installer can create an isolated environment for each one:

```python
# my_plugin.py

def register(registry):
    registry.add_dependency("requests>=2.0")
    registry.register_ui_component("hello", lambda: print("Hello!"))
```

To distribute the plugin as a package, declare an entry point in `pyproject.toml`:

```toml
[project.entry-points."installer_plugins"]
"my-plugin" = "my_plugin:register"
```

## Loading Plugins

Use :func:`discover_plugins` to load all available plugins:

```python
from installer.plugins import discover_plugins

registry = discover_plugins("./local_plugins")
print(registry.dependencies)  # mapping of plugin name -> set(dependencies)
print(registry.ui_components)
```

The returned registry lists all requested dependencies and registered UI
components so the installer can act on them.
