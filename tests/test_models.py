import hashlib

from installer import models


def _fake_urlopen_factory(data: bytes, failures: int = 1):
    """Create a ``urlopen`` replacement that fails ``failures`` times mid-stream."""

    state = {"calls": 0, "timeouts": []}

    def _fake_urlopen(req, timeout=None):
        # Determine starting offset via Range header
        start = 0
        if hasattr(req, "headers"):
            range_header = req.headers.get("Range")
            if range_header:
                start = int(range_header.split("=")[1].split("-")[0])

        state["timeouts"].append(timeout)
        fail = state["calls"] < failures
        state["calls"] += 1

        class Resp:
            def __init__(self):
                self.pos = start

            def read(self, n=-1):
                if fail and self.pos >= 4:
                    raise models.urllib.error.URLError("boom")
                end = len(data) if n < 0 else self.pos + n
                chunk = data[self.pos:end]
                self.pos += len(chunk)
                return chunk

            def getheader(self, name, default=None):
                if name.lower() == "content-length":
                    return str(len(data) - start)
                if name.lower() == "content-range":
                    return f"bytes {start}-{len(data)-1}/{len(data)}"
                return default

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                pass

        return Resp()

    return _fake_urlopen, state


def test_compatible_models(monkeypatch):
    dummy = {
        "cpu": models.ModelInfo(
            name="cpu",
            filename="cpu.bin",
            checksum="",
            host="default",
            requires_gpu=False,
            min_ram_gb=4,
        ),
        "gpu": models.ModelInfo(
            name="gpu",
            filename="gpu.bin",
            checksum="",
            host="default",
            requires_gpu=True,
            min_vram_gb=8,
        ),
    }
    monkeypatch.setattr(models, "MODEL_REGISTRY", dummy)
    info = {"gpu_name": None, "ram_total_gb": 16, "gpu_vram_gb": None}
    compatibles = models.compatible_models(info)
    assert [m.name for m in compatibles] == ["cpu"]


def test_model_url(monkeypatch):
    monkeypatch.setitem(models.MODEL_HOSTS, "test", "https://example.org/base")
    info = models.ModelInfo(
        name="dummy",
        filename="dummy.bin",
        checksum="",
        host="test",
    )
    assert info.url == "https://example.org/base/dummy.bin"


def test_verify_checksum(tmp_path):
    data = b"hello"
    file = tmp_path / "model.bin"
    file.write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    assert models.verify_checksum(file, digest)
    assert not models.verify_checksum(file, "0" * 64)


def test_download_model_retries(tmp_path, monkeypatch):
    data = b"abcdefghij"
    checksum = hashlib.sha256(data).hexdigest()
    info = models.ModelInfo(
        name="test",
        filename="test.bin",
        checksum=checksum,
    )
    monkeypatch.setattr(models, "MODEL_REGISTRY", {"test": info})

    fake_urlopen, state = _fake_urlopen_factory(data, failures=2)
    monkeypatch.setattr(models.urllib.request, "urlopen", fake_urlopen)

    sleeps: list[float] = []
    monkeypatch.setattr(models.time, "sleep", lambda s: sleeps.append(s))

    dest = models.download_model("test", tmp_path, retries=3, timeout=1)

    assert dest.read_bytes() == data
    # Two retries should have occurred with exponential backoff (1s then 2s)
    assert sleeps == [1, 2]
    # Ensure timeout was forwarded to urlopen for each attempt
    assert state["timeouts"] == [1, 1, 1]
