from windows_ai.provider_cli_executor import ProviderCLIExecutor


def test_ollama_payload_includes_num_predict_when_max_tokens_set():
    payload = ProviderCLIExecutor()._build_ollama_chat_payload(
        model_name="phi3:mini",
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.5,
        max_tokens=42,
        stream=False,
    )
    assert payload["model"] == "phi3:mini"
    assert payload["stream"] is False
    assert payload["options"]["temperature"] == 0.5
    assert payload["options"]["num_predict"] == 42


def test_ollama_payload_omits_num_predict_when_max_tokens_unset():
    payload = ProviderCLIExecutor()._build_ollama_chat_payload(
        model_name="llama3.1:8b",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.2,
        max_tokens=None,
        stream=True,
    )
    assert payload["model"] == "llama3.1:8b"
    assert payload["stream"] is True
    assert payload["options"]["temperature"] == 0.2
    assert "num_predict" not in payload["options"]
