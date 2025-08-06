import json
from installer import env


def test_remove_env_deletes_directory_and_record(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    monkeypatch.setattr(env, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(env, "BASE_DIR", config_dir / "venvs")
    monkeypatch.setattr(env, "ENV_RECORD_FILE", config_dir / "envs.json")

    env_dir = env.BASE_DIR / "sample"
    env_dir.mkdir(parents=True)

    env.ENV_RECORD_FILE.write_text(json.dumps({"sample": str(env_dir)}))

    env.remove_env("sample")

    assert not env_dir.exists()
    assert not env.ENV_RECORD_FILE.exists()
