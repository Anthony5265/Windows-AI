# Plugin Marketplace Contribution Guide

This project includes a lightweight plugin marketplace.  Plugins allow users to
extend the Control Center with new capabilities such as model integrations or
automation tools.  Community contributions are welcome—use the guidelines below
to add your plugin.

## Adding a Plugin

1. Edit `plugins/catalog.json` and append a new entry under the `plugins`
   array.  Each entry must provide:

   - `name` – unique plugin name.
   - `description` – short human readable summary.
   - `command` – installation command.  Prefer absolute paths or one of the
     approved commands (`pip`, `npm`, `brew`).
   - `paid` – whether the plugin requires a commercial licence.
   - `metadata` – free form dictionary with fields such as `version` or
     `author`.
   - `rating` – community rating between 0 and 5.
   - `dependencies` – list of other plugin names that must be installed first.

2. If your plugin distribution can be verified, include a `signature` field
   containing the SHA256 hash of the plugin name.  This simple scheme is used
   by the test suite to demonstrate signature verification.

3. Provide accompanying documentation or usage examples where appropriate.

## Testing

Run the unit tests to ensure your plugin works with the manager:

```bash
pytest tests/test_plugin_manager.py
```

Plugins that fail to install or break existing tests will not be accepted.

## Security

Installation commands execute inside a temporary sandbox directory with a very
limited environment.  Avoid commands that modify global system state and do not
rely on environment variables beyond `PATH`.

