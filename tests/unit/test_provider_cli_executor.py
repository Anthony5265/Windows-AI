import pathlib

from windows_ai.provider_cli_executor import ProviderCLIExecutor, ProviderCLIExecutionError


def test_build_cli_command_candidates_for_codex_includes_fallbacks():
    executor = ProviderCLIExecutor()
    candidates = executor._build_cli_command_candidates(
        provider_id="codex",
        executable=pathlib.Path("C:/Tools/codex.exe"),
        prompt="hello world",
        temperature=0.4,
        max_tokens=256,
    )

    assert len(candidates) >= 3
    first_command, first_inline = candidates[0]
    assert first_command[:3] == ["C:/Tools/codex.exe", "chat", "--prompt"]
    assert first_command[-4:] == ["hello world", "--max-tokens", "256", "--temperature", "0.4"][-4:]
    assert first_inline is True

    assert any(candidate[0][:2] == ["C:/Tools/codex.exe", "chat"] and candidate[1] is False for candidate in candidates)


def test_build_cli_command_candidates_rejects_unknown_provider():
    executor = ProviderCLIExecutor()
    try:
        executor._build_cli_command_candidates(
            provider_id="unknown",
            executable=pathlib.Path("/tmp/unknown"),
            prompt="hello",
            temperature=0.7,
            max_tokens=None,
        )
    except ProviderCLIExecutionError as exc:
        assert "No command template configured" in str(exc)
    else:
        raise AssertionError("Expected ProviderCLIExecutionError for unknown provider")


def test_messages_to_prompt_formats_roles_and_content():
    executor = ProviderCLIExecutor()
    prompt = executor._messages_to_prompt([
        {"role": "system", "content": "You are concise."},
        {"role": "user", "content": "Summarize this."},
        {"role": "assistant", "content": "Sure."},
    ])

    assert "SYSTEM:\nYou are concise." in prompt
    assert "USER:\nSummarize this." in prompt
    assert "ASSISTANT:\nSure." in prompt


def test_normalize_cli_output_extracts_nested_message_content():
    executor = ProviderCLIExecutor()
    output = '{"message": {"content": "Hello from nested json"}}'
    assert executor._normalize_cli_output(output) == "Hello from nested json"


def test_normalize_cli_output_extracts_choice_message_content():
    executor = ProviderCLIExecutor()
    output = '{"choices": [{"message": {"content": "Hello from choices"}}]}'
    assert executor._normalize_cli_output(output) == "Hello from choices"


def test_normalize_cli_output_parses_last_json_line():
    executor = ProviderCLIExecutor()
    output = "debug line\n{\"response\": \"Recovered from trailing json\"}"
    assert executor._normalize_cli_output(output) == "Recovered from trailing json"


def test_normalize_cli_output_falls_back_to_plain_text():
    executor = ProviderCLIExecutor()
    output = "Plain text response"
    assert executor._normalize_cli_output(output) == "Plain text response"
