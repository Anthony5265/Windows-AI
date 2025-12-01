# Updater

The `updater` package provides a light‑weight mechanism for keeping the
Windows AI installation up to date.  Updates follow a three step
process:

1. **Version check** – `Updater.latest_version()` fetches metadata from
the update server and compares it with the currently installed version.
2. **Download and verification** – `Updater.download()` retrieves the
update package while `Updater.verify_signature()` validates the SHA256
signature published alongside the release.
3. **Install with rollback** – `Updater.apply_update()` snapshots the
existing installation, invokes the PowerShell scripts in the
`install/` directory and restores the snapshot if the installation
fails.

The `ChatGUI` exposes these features through *Settings → Updates* where
release notes for the latest version are displayed.
