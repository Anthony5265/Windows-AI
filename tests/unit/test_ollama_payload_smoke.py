from windows_ai.provider_cli_executor import ProviderCLIExecutor


def test_ollama_payload_smoke():
    payload = ProviderCLIExecutor()._build_ollama_chat_payload(
        model_name="phi3:mini",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.5,
        max_tokens=42,
        stream=False,
    )
    assert payload["options"]["num_predict"] == 42
