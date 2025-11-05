# Rollback and Snapshot Removal

The installer and updater capture configuration snapshots before modifying
system files. Each snapshot is associated with a feature name and stored in
`~/.windows_ai/snapshots`.

## Rolling back

When an installation or update fails, the modules restore the affected feature
from its snapshot:

```python
from snapshot import rollback
rollback("install")
```

## Removing snapshots

Successful operations automatically remove their snapshots. Snapshots can also
be removed manually:

```python
from snapshot import remove
remove("install")
```

Deleting the `snapshots` directory will remove all stored backups.
