import hashlib
from pathlib import Path

import pytest

from updater import Updater


def make_signed_server(tmp_path: Path, version: str, data: bytes) -> str:
    base = tmp_path / "server"
    pkg_dir = base / version
    pkg_dir.mkdir(parents=True)
    pkg_path = pkg_dir / "package.zip"
    pkg_path.write_bytes(data)
    sig = hashlib.sha256(data).hexdigest()
    (pkg_dir / "package.sig").write_text(sig)
    return base.as_uri()


def test_fetch_signed_package(tmp_path):
    data = b"payload"
    base = make_signed_server(tmp_path, "1.0", data)
    updater = Updater(base_url=base)
    pkg = updater.fetch_signed_package("1.0", tmp_path / "pkg.zip")
    assert pkg.read_bytes() == data


def test_fetch_signed_package_invalid(tmp_path):
    data = b"payload"
    base = make_signed_server(tmp_path, "1.0", data)
    # Corrupt signature
    (tmp_path / "server" / "1.0" / "package.sig").write_text("0" * 64)
    updater = Updater(base_url=base)
    with pytest.raises(ValueError):
        updater.fetch_signed_package("1.0", tmp_path / "pkg.zip")
