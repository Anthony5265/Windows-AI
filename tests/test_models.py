import hashlib

from installer import models


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
