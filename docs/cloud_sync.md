# Cloud Sync

The `cloud_sync` module provides a lightweight interface for backing up user
profiles and downloaded models to cloud providers.  Data is encrypted with a
password before leaving the local machine.  The default implementation ships
with an in-memory provider used for testing, while real deployments can supply
implementations for services like S3, Dropbox or Google Drive.

## Basic Usage

```python
from cloud_sync import CloudSync, InMemoryProvider

provider = InMemoryProvider()
sync = CloudSync(provider, password="secret", conflict_resolution="local")

sync.backup_file("profile.json", "profile")
```

## Conflict Resolution

`CloudSync.sync_file` compares local and remote copies.  When both differ the
`conflict_resolution` policy determines the outcome:

- `"local"` – upload the local file over the remote copy.
- `"remote"` – overwrite the local file with the remote version.
- `"ask"` – raise a `RuntimeError` signalling a conflict.

This behaviour is exposed in the Control Center GUI where users can also
configure the sync frequency.
