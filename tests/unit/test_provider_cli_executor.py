import asyncio
import importlib
import json
import pathlib
import sys
import types

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from windows_ai.provider_cli_executor import ProviderCLIExecutor, ProviderCLIExecutionError, ProviderChatResult
import windows_ai.provider_cli_registry as provider_cli_registry_module


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


def test_normalize_stream_chunk_extracts_nested_message_content():
    executor = ProviderCLIExecutor()
    chunk = '{"message": {"content": "Hello from streamed json"}}\n'
    assert executor._normalize_stream_chunk(chunk) == "Hello from streamed json"


def test_normalize_stream_chunk_falls_back_to_plain_text():
    executor = ProviderCLIExecutor()
    chunk = "Hello from streamed text\n"
    assert executor._normalize_stream_chunk(chunk) == "Hello from streamed text\n"


async def _collect_stream(executor, target_model, messages):
    chunks = []
    async for chunk in executor.execute_chat_stream(target_model=target_model, messages=messages):
        chunks.append(chunk)
    return chunks


def test_execute_chat_stream_uses_cli_stream_path(monkeypatch):
    executor = ProviderCLIExecutor()

    async def fake_stream_cli_chat(*args, **kwargs):
        yield "chunk one"
        yield "chunk two"

    monkeypatch.setattr(executor, "_stream_cli_chat", fake_stream_cli_chat)
    chunks = asyncio.run(_collect_stream(executor, "cli:codex", [{"role": "user", "content": "hi"}]))
    assert chunks == ["chunk one", "chunk two"]


def test_execute_chat_stream_uses_non_ollama_fallback(monkeypatch):
    executor = ProviderCLIExecutor()

    async def fake_execute_chat(*args, **kwargs):
        class _Result:
            content = "fallback streamed content"
        return _Result()

    monkeypatch.setattr(executor, "execute_chat", fake_execute_chat)

    async def fake_stream_cli_chat(*args, **kwargs):
        result = await executor.execute_chat(target_model="cli:codex", messages=[{"role": "user", "content": "hi"}])
        yield result.content

    monkeypatch.setattr(executor, "_stream_cli_chat", fake_stream_cli_chat)
    chunks = asyncio.run(_collect_stream(executor, "cli:codex", [{"role": "user", "content": "hi"}]))
    assert chunks == ["fallback streamed content"]


def test_extract_text_from_dict_supports_output_key():
    executor = ProviderCLIExecutor()
    parsed = {"output": "Hello from output key"}
    assert executor._extract_text_from_dict(parsed) == "Hello from output key"


def _build_provider_chat_client(monkeypatch):
    fake_integrations_module = types.ModuleType("windows_ai.integrations")
    fake_integrations_module.router = APIRouter(prefix="/integrations", tags=["integrations"])
    monkeypatch.setitem(sys.modules, "windows_ai.integrations", fake_integrations_module)

    reloaded_registry_module = importlib.reload(provider_cli_registry_module)

    app = FastAPI()
    app.include_router(fake_integrations_module.router)
    return reloaded_registry_module, TestClient(app)


def test_provider_chat_route_returns_provider_result(monkeypatch):
    registry_module, client = _build_provider_chat_client(monkeypatch)
    captured = {}

    async def fake_execute_chat(*, target_model, messages, temperature, max_tokens):
        captured["target_model"] = target_model
        captured["messages"] = messages
        captured["temperature"] = temperature
        captured["max_tokens"] = max_tokens
        return ProviderChatResult(
            model=target_model,
            provider_id="codex",
            content="hello from provider route",
            backend="provider-cli",
            metadata={"source": "test"},
        )

    monkeypatch.setattr(registry_module.provider_cli_executor, "execute_chat", fake_execute_chat)

    response = client.post(
        "/integrations/providers/chat",
        json={
            "message": "hi there",
            "conversation_id": "conv-123",
            "model": "cli:codex",
            "temperature": 0.2,
            "max_tokens": 64,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["conversation_id"] == "conv-123"
    assert body["message"]["content"] == "hello from provider route"
    assert body["provider_result"]["provider_id"] == "codex"
    assert captured["target_model"] == "cli:codex"
    assert captured["messages"] == [{"role": "user", "content": "hi there"}]
    assert captured["temperature"] == 0.2
    assert captured["max_tokens"] == 64


def test_provider_chat_route_does_not_leak_history_between_requests(monkeypatch):
    registry_module, client = _build_provider_chat_client(monkeypatch)
    captured_messages = []

    async def fake_execute_chat(*, target_model, messages, temperature, max_tokens):
        captured_messages.append(messages)
        return ProviderChatResult(
            model=target_model,
            provider_id="codex",
            content="ok",
            backend="provider-cli",
            metadata={},
        )

    monkeypatch.setattr(registry_module.provider_cli_executor, "execute_chat", fake_execute_chat)

    first_response = client.post(
        "/integrations/providers/chat",
        json={
            "message": "first request",
            "model": "cli:codex",
        },
    )
    second_response = client.post(
        "/integrations/providers/chat",
        json={
            "message": "second request",
            "model": "cli:codex",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert captured_messages == [
        [{"role": "user", "content": "first request"}],
        [{"role": "user", "content": "second request"}],
    ]


def test_provider_chat_route_avoids_duplicate_final_user_message(monkeypatch):
    registry_module, client = _build_provider_chat_client(monkeypatch)
    captured = {}

    async def fake_execute_chat(*, target_model, messages, temperature, max_tokens):
        captured["messages"] = messages
        return ProviderChatResult(
            model=target_model,
            provider_id="codex",
            content="history respected",
            backend="provider-cli",
            metadata={},
        )

    monkeypatch.setattr(registry_module.provider_cli_executor, "execute_chat", fake_execute_chat)

    history = [
        {"role": "assistant", "content": "Earlier summary"},
        {"role": "user", "content": "repeat this"},
    ]
    response = client.post(
        "/integrations/providers/chat",
        json={
            "message": "repeat this",
            "model": "cli:codex",
            "history": history,
        },
    )

    assert response.status_code == 200
    assert captured["messages"] == history
    assert response.json()["message"]["content"] == "history respected"


def test_provider_chat_route_returns_error_payload_on_execution_failure(monkeypatch):
    registry_module, client = _build_provider_chat_client(monkeypatch)

    async def fake_execute_chat(*, target_model, messages, temperature, max_tokens):
        raise ProviderCLIExecutionError("provider unavailable")

    monkeypatch.setattr(registry_module.provider_cli_executor, "execute_chat", fake_execute_chat)

    response = client.post(
        "/integrations/providers/chat",
        json={
            "message": "hi there",
            "conversation_id": "conv-err",
            "model": "cli:codex",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["conversation_id"] == "conv-err"
    assert body["error"] == "provider unavailable"


def test_provider_chat_route_honors_stream_flag(monkeypatch):
    registry_module, client = _build_provider_chat_client(monkeypatch)

    async def fail_execute_chat(*, target_model, messages, temperature, max_tokens):
        raise AssertionError("execute_chat should not be called when stream=true")

    async def fake_execute_chat_stream(*, target_model, messages, temperature, max_tokens):
        assert target_model == "cli:codex"
        assert messages == [{"role": "user", "content": "stream on main route"}]
        assert temperature == 0.7
        assert max_tokens is None
        yield "chunk a"
        yield "chunk b"

    monkeypatch.setattr(registry_module.provider_cli_executor, "execute_chat", fail_execute_chat)
    monkeypatch.setattr(registry_module.provider_cli_executor, "execute_chat_stream", fake_execute_chat_stream)

    response = client.post(
        "/integrations/providers/chat",
        json={
            "message": "stream on main route",
            "conversation_id": "conv-main-stream",
            "model": "cli:codex",
            "stream": True,
        },
    )

    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.strip().splitlines()]
    assert [event["type"] for event in events] == ["start", "chunk", "chunk", "complete"]
    assert events[0]["conversation_id"] == "conv-main-stream"
    assert events[1]["content"] == "chunk a"
    assert events[2]["content"] == "chunk b"
    assert events[3]["content"] == "chunk achunk b"


def test_provider_chat_stream_route_returns_ndjson_events(monkeypatch):
    registry_module, client = _build_provider_chat_client(monkeypatch)

    async def fake_execute_chat_stream(*, target_model, messages, temperature, max_tokens):
        assert target_model == "cli:codex"
        assert messages == [{"role": "user", "content": "stream this"}]
        assert temperature == 0.7
        assert max_tokens is None
        yield "chunk one "
        yield "chunk two"

    monkeypatch.setattr(registry_module.provider_cli_executor, "execute_chat_stream", fake_execute_chat_stream)

    response = client.post(
        "/integrations/providers/chat/stream",
        json={
            "message": "stream this",
            "conversation_id": "conv-stream",
            "model": "cli:codex",
        },
    )

    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.strip().splitlines()]
    assert [event["type"] for event in events] == ["start", "chunk", "chunk", "complete"]
    assert events[0]["conversation_id"] == "conv-stream"
    assert events[1]["content"] == "chunk one "
    assert events[2]["content"] == "chunk two"
    assert events[3]["content"] == "chunk one chunk two"


def test_provider_chat_stream_route_emits_error_event(monkeypatch):
    registry_module, client = _build_provider_chat_client(monkeypatch)

    async def fake_execute_chat_stream(*, target_model, messages, temperature, max_tokens):
        raise ProviderCLIExecutionError("stream failed")
        yield "unreachable"

    monkeypatch.setattr(registry_module.provider_cli_executor, "execute_chat_stream", fake_execute_chat_stream)

    response = client.post(
        "/integrations/providers/chat/stream",
        json={
            "message": "stream this",
            "conversation_id": "conv-error",
            "model": "cli:codex",
        },
    )

    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.strip().splitlines()]
    assert [event["type"] for event in events] == ["start", "error"]
    assert events[1]["error"] == "stream failed"
    assert events[1]["conversation_id"] == "conv-error"


def test_provider_registry_marks_ollama_ready_without_cloud_auth(monkeypatch):
    registry = provider_cli_registry_module.ProviderCLIRegistry()

    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.setattr(registry, "_locate_executable", lambda provider_id, executable_names: pathlib.Path("/tmp/ollama"))
    monkeypatch.setattr(registry, "_get_version", lambda executable_path: "ollama 0.6.0")

    result = registry.detect_provider("ollama")

    assert result.detected is True
    assert result.auth_configured is True
    assert result.recommended_action == "ready"
    assert result.version == "ollama 0.6.0"


def test_provider_registry_marks_detected_cloud_cli_for_auth_when_key_missing(monkeypatch):
    registry = provider_cli_registry_module.ProviderCLIRegistry()

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(registry, "_locate_executable", lambda provider_id, executable_names: pathlib.Path("/tmp/codex"))
    monkeypatch.setattr(registry, "_get_version", lambda executable_path: "codex 1.2.3")

    result = registry.detect_provider("codex")

    assert result.detected is True
    assert result.auth_configured is False
    assert result.recommended_action == "authenticate"
    assert result.version == "codex 1.2.3"
