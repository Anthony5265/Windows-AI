# Uninstalling and Rolling Back Windows AI

If you need to remove Windows AI or revert system changes, use the snapshot and uninstall tools that ship with the project.

## Automated Uninstall
Run the PowerShell script:

```powershell
install/uninstall.ps1
```

The script reads the snapshot created during installation and removes any services and firewall rules that were added.

## Rollback from a Snapshot
1. Open the Control Center.
2. Navigate to **Snapshots**.
3. Select a snapshot and choose **Restore** to revert the environment.

Snapshots are stored under `~/.windows_ai/`. Creating a snapshot before major changes allows you to restore your system at any time.
