import logging
import pytest
from installer import models


class DummyResponse:
    def __init__(self, data: bytes):
        self._data = data
        self._idx = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def read(self, size: int):
        if self._idx >= len(self._data):
            return b""
        chunk = self._data[self._idx : self._idx + size]
        self._idx += len(chunk)
        return chunk

    def getheader(self, name, default=None):
        if name == "Content-Length":
            return str(len(self._data))
        return default


def test_checksum_failure_deletes_file(tmp_path, monkeypatch, caplog):
    data = b"corrupt"
    model = models.ModelInfo(
        name="bad",
        filename="bad.bin",
        checksum="0" * 64,
    )
    monkeypatch.setattr(models, "MODEL_REGISTRY", {"bad": model})
    monkeypatch.setattr(
        models.urllib.request, "urlopen", lambda *args, **kwargs: DummyResponse(data)
    )
    monkeypatch.setattr(models.urllib.request, "urlopen", lambda url, timeout=None: DummyResponse(data))

    caplog.set_level(logging.WARNING)
    with pytest.raises(ValueError):
        models.download_model("bad", tmp_path)

    dest = tmp_path / model.filename
    assert not dest.exists()
    assert any("deleting" in r.message for r in caplog.records)


def test_verify_checksum_deletes_and_logs(tmp_path, caplog):
    file = tmp_path / "bad.bin"
    file.write_bytes(b"bad")
    caplog.set_level(logging.WARNING)
    assert not models.verify_checksum(file, "0" * 64)
    assert not file.exists()
    assert any("deleting" in r.message for r in caplog.records)
