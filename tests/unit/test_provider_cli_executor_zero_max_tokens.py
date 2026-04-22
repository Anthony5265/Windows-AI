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
