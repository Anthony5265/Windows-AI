# Rollback and Uninstall

Windows AI records the system changes performed during installation so that they can be undone later.

## Snapshots

Running the installer creates a snapshot file under `~/.windows_ai/` that lists the services and firewall rules added by the setup process.
Use the Control Center's **Snapshot** button to manually create a snapshot before making further changes and **Restore** to revert the environment.

## Uninstall

The `install/uninstall.ps1` script reads the snapshot and removes any recorded services and firewall rules, returning the machine to its previous state.
