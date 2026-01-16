# Cloud Sync (Placeholder)

This stub provides a minimal `CloudSyncProvider` that mirrors files between local paths. Extend it with real cloud SDK bindings when ready.

Usage example:

```python
from cloud_sync import CloudSyncProvider
from pathlib import Path

provider = CloudSyncProvider("./cloud_sync_store")
provider.sync([Path("./example.txt")], "./synced")
```
