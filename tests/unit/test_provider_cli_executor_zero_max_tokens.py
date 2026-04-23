import pathlib

from windows_ai.provider_cli_executor import ProviderCLIExecutor


def test_cli_command_candidates_preserve_zero_max_tokens():
    candidates = ProviderCLIExecutor()._build_cli_command_candidates(
        provider_id="codex",
        executable=pathlib.Path("C:/Tools/codex.exe"),
        prompt="hello",
        temperature=0.4,
        max_tokens=0,
    )

    first_command, _first_inline = candidates[0]
    assert "--max-tokens" in first_command
    assert "0" in first_command


def test_cli_command_candidates_include_flag_free_fallback_variant():
    candidates = ProviderCLIExecutor()._build_cli_command_candidates(
        provider_id="codex",
        executable=pathlib.Path("C:/Tools/codex.exe"),
        prompt="hello",
        temperature=0.4,
        max_tokens=64,
    )

    command_argvs = [candidate[0] for candidate in candidates]
    assert ["C:/Tools/codex.exe", "chat", "--prompt", "hello"] in command_argvs
    assert ["C:/Tools/codex.exe", "chat", "--prompt", "hello", "--max-tokens", "64", "--temperature", "0.4"] in command_argvs
