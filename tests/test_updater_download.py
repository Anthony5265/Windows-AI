import hashlib
from pathlib import Path

import pytest

from updater import Updater


def make_server(tmp_path: Path, version: str, data: bytes) -> tuple[str, str]:
    """Create a fake update server structure returning (base_url, checksum)."""
    base = tmp_path / "server"
    pkg_dir = base / version
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "package.zip").write_bytes(data)
    checksum = hashlib.sha256(data).hexdigest()
    return base.as_uri(), checksum


def test_download_emits_progress(tmp_path):
    data = b"a" * 20000
    base_url, checksum = make_server(tmp_path, "1.0", data)
    dest = tmp_path / "pkg.zip"
    updater = Updater(base_url=base_url)
    calls: list[tuple[int, int]] = []

    def progress(downloaded: int, total: int) -> None:
        calls.append((downloaded, total))

    updater.download("1.0", dest, progress=progress, checksum=checksum)

    assert calls, "progress callback was not invoked"
    assert calls[-1] == (len(data), len(data))
    assert dest.read_bytes() == data


def test_download_checksum_failure(tmp_path):
    data = b"test"
    base_url, checksum = make_server(tmp_path, "2.0", data)
    dest = tmp_path / "pkg.zip"
    updater = Updater(base_url=base_url)

    with pytest.raises(ValueError):
        updater.download("2.0", dest, checksum="0" * 64)

    assert not dest.exists()
