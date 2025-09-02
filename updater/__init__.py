"""Update management for Windows AI.

This module provides utilities to check for new versions, download
update packages, verify cryptographic signatures, and apply updates
with snapshot and rollback support.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Callable
from urllib.request import urlopen

__all__ = ["Updater"]


class Updater:
    """Light‑weight update helper.

    Parameters
    ----------
    base_url:
        Base URL where update metadata and packages are hosted.
    install_dir:
        Directory where the application is installed.  Snapshots are
        created from this path before applying updates so that a failed
        installation can be rolled back.
    install_script / rollback_script:
        Paths to the PowerShell scripts in :mod:`install/` that perform
        installation and rollback operations.  The methods default to the
        repository's scripts but are easily monkey‑patched during tests.
    """

    def __init__(
        self,
        base_url: str = "https://example.com/updates",
        install_dir: Path | str | None = None,
        install_script: Path | str = Path("install/install.ps1"),
        rollback_script: Path | str = Path("install/uninstall.ps1"),
        current_version: str = "0.0.0",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.install_dir = Path(install_dir or Path.cwd())
        self.install_script = Path(install_script)
        self.rollback_script = Path(rollback_script)
        self.current_version = current_version

    # ------------------------------------------------------------------
    # Version handling
    def latest_version(self) -> str:
        """Return the latest available version.

        Network failures simply return the current version so that the
        GUI can show a sensible default when offline.
        """

        try:  # pragma: no cover - network access
            with urlopen(f"{self.base_url}/latest") as fh:
                return fh.read().decode().strip()
        except Exception:  # pragma: no cover - offline fallback
            return self.current_version

    def download(
        self,
        version: str,
        dest: Path | str,
        progress: Callable[[int, int], None] | None = None,
        checksum: str | None = None,
    ) -> Path:
        """Download the update package for *version* to *dest*.

        Parameters
        ----------
        version:
            Version identifier to download or a direct URL.
        dest:
            Destination file path.
        progress:
            Optional callback receiving ``bytes_downloaded`` and
            ``total_bytes`` for progress reporting.
        checksum:
            Expected SHA256 checksum of the file. If provided, the
            downloaded data is verified and a :class:`ValueError` is
            raised on mismatch.
        """

        dest_path = Path(dest)
        if version.startswith("http://") or version.startswith("https://"):
            url = version
        else:
            url = f"{self.base_url}/{version}/package.zip"
        with urlopen(url) as resp:
            header = None
            if hasattr(resp, "getheader"):
                try:
                    header = resp.getheader("Content-Length")
                except Exception:
                    header = None
            elif hasattr(resp, "headers"):
                header = resp.headers.get("Content-Length")
            total = int(header or 0)
            downloaded = 0
            sha = hashlib.sha256()
            with open(dest_path, "wb") as fh:
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    fh.write(chunk)
                    sha.update(chunk)
                    downloaded += len(chunk)
                    if progress:
                        progress(downloaded, total)

        if checksum and sha.hexdigest().lower() != checksum.lower():
            dest_path.unlink(missing_ok=True)
            raise ValueError("Checksum mismatch for downloaded package")

        return dest_path

    def install_framework(
        self,
        name: str,
        version: str,
        model_urls: list[str] | None = None,
        models_dir: Path | str | None = None,
    ) -> None:
        """Install a Python framework and optional models.

        Parameters
        ----------
        name:
            Package name to install via ``pip``.
        version:
            Package version specifier.
        model_urls:
            Optional list of model URLs to download.
        models_dir:
            Target directory for downloaded models. Defaults to
            ``install_dir / 'models'``.
        """

        env = os.environ.copy()
        env.update(
            {
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_NO_INPUT": "1",
                "PYTHONPATH": "",
            }
        )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", f"{name}=={version}"],
            check=True,
            env=env,
        )

        if model_urls:
            target = Path(models_dir or self.install_dir / "models")
            target.mkdir(parents=True, exist_ok=True)
            for url in model_urls:
                dest = target / Path(url).name
                self.download(url, dest)

    def verify_checksum(self, file_path: Path | str, expected: str) -> bool:
        """Verify the SHA256 checksum of ``file_path`` against ``expected``."""

        h = hashlib.sha256()
        with open(file_path, "rb") as fh:
            for chunk in iter(lambda: fh.read(8192), b""):
                h.update(chunk)
        return h.hexdigest().lower() == expected.lower()

    def verify_signature(self, file_path: Path | str, version: str) -> bool:
        """Verify the SHA256 signature of *file_path* for *version*."""

        file_path = Path(file_path)
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        try:  # pragma: no cover - network access
            with urlopen(f"{self.base_url}/{version}/package.sig") as fh:
                signature = fh.read().decode().strip()
        except Exception:  # pragma: no cover - offline fallback
            return False
        return digest == signature

    def get_release_notes(self, version: str) -> str:
        """Retrieve release notes for *version*."""

        try:  # pragma: no cover - network access
            with urlopen(f"{self.base_url}/{version}/notes.txt") as fh:
                return fh.read().decode()
        except Exception:  # pragma: no cover - offline fallback
            return "No release notes available."

    # ------------------------------------------------------------------
    # Snapshot and rollback
    def _snapshot_path(self) -> Path:
        return Path(tempfile.mkdtemp(prefix="waisnap_"))

    def create_snapshot(self) -> Path:
        """Create a snapshot of the install directory and return it."""

        snap = self._snapshot_path()
        if self.install_dir.exists():
            shutil.copytree(self.install_dir, snap / "install", dirs_exist_ok=True)
        return snap

    def rollback(self, snapshot: Path) -> None:
        """Restore the install directory from *snapshot*."""

        try:
            self.run_uninstall()
        finally:
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
            shutil.copytree(snapshot / "install", self.install_dir, dirs_exist_ok=True)

    # ------------------------------------------------------------------
    # Installation helpers
    def run_install(self, package: Path | str) -> None:
        """Invoke the PowerShell installer."""

        if not self.install_script.exists():
            raise FileNotFoundError(self.install_script)
        subprocess.run(["pwsh", str(self.install_script), str(package)], check=True)

    def run_uninstall(self) -> None:
        """Invoke the PowerShell rollback script if it exists."""

        if self.rollback_script.exists():
            subprocess.run(["pwsh", str(self.rollback_script)], check=True)

    def apply_update(
        self, package: Path | str, checksum: str | None = None
    ) -> None:
        """Apply an update package with automatic rollback on failure.

        Parameters
        ----------
        package:
            Path to the update package to install.
        checksum:
            Optional expected SHA256 hash. If provided, the package is
            verified before installation and a :class:`ValueError` is
            raised when it does not match.
        """

        package_path = Path(package)
        if checksum and not self.verify_checksum(package_path, checksum):
            raise ValueError("Checksum mismatch for package")

        snapshot = self.create_snapshot()
        try:
            self.run_install(package_path)
        except Exception:
            self.rollback(snapshot)
            raise
