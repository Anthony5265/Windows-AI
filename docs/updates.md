# Updates

The update system ensures that Windows AI can be refreshed without risking a broken installation.

## Flow

1. **Version discovery** – `Updater.latest_version()` checks the update service for the most recent build.
2. **Signed package fetch** – `Updater.fetch_signed_package()` downloads the release archive and validates its SHA256 signature.
3. **Snapshot** – before installing, `Updater.apply_update()` captures the current installation so that it can be restored if something goes wrong.
4. **Install** – the PowerShell script in `install/install.ps1` is executed to apply the update.
5. **Rollback** – on any failure the snapshot is automatically restored using `Updater.rollback()`.

To update programmatically:

```python
from updater import Updater

updater = Updater()
latest = updater.latest_version()
updater.update(latest)
```

The installer helpers in `installer/env_setup.py` expose this functionality via the `update` flag on `setup_all`, allowing environments to be refreshed before dependency installation.
