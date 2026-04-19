"""Execution layer for provider-backed chat targets.

This module turns detected provider/runtime targets into callable chat backends for
Windows AI. It is intentionally conservative and best-effort:
- fixed provider ids only
- no arbitrary command execution from user input
- generic CLI invocation patterns where vendor-specific SDKs are unavailable

Supported target formats:
- cli:gemini
- cli:codex
- cli:claude
- cli:grok
- ollama:<model>
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
import json
import os

import httpx

from windows_ai.provider_cli_registry import provider_cli_registry


@dataclass
class ProviderChatResult:
    model: str
    provider_id: str
    content: str
    backend: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProviderCLIExecutionError(RuntimeError):
    pass


class ProviderCLIExecutor:
    def __init__(self) -> None:
        self.ollama_base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
        self.timeout_seconds = int(os.getenv("WINDOWS_AI_PROVIDER_TIMEOUT", "90"))

    async def execute_chat(
        self,
        target_model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> ProviderChatResult:
        if target_model.startswith("ollama:"):
            return await self._execute_ollama_chat(target_model, messages, temperature)
        if target_model.startswith("cli:"):
            provider_id = target_model.split(":", 1)[1]
            return await self._execute_cli_chat(provider_id, target_model, messages, temperature, max_tokens)
        raise ProviderCLIExecutionError(f"Unsupported provider target: {target_model}")

    async def _execute_ollama_chat(
        self,
        target_model: str,
        messages: List[Dict[str, str]],
        temperature: float,
    ) -> ProviderChatResult:
        model_name = target_model.split(":", 1)[1]
        url = f"{self.ollama_base_url}/api/chat"
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        content = (
            data.get("message", {}).get("content")
            or data.get("response")
            or ""
        ).strip()
        if not content:
            raise ProviderCLIExecutionError("Ollama returned an empty response")

        return ProviderChatResult(
            model=target_model,
            provider_id="ollama",
            content=content,
            backend="ollama-http",
            metadata={
                "ollama_model": model_name,
                "done": data.get("done", True),
                "total_duration": data.get("total_duration"),
            },
        )

    async def _execute_cli_chat(
        self,
        provider_id: str,
        target_model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> ProviderChatResult:
        detection = provider_cli_registry.detect_provider(provider_id)
        if not detection.detected or not detection.executable_path:
            raise ProviderCLIExecutionError(f"Provider CLI not detected: {provider_id}")

        prompt = self._messages_to_prompt(messages)
        executable = Path(detection.executable_path)
        command = self._build_cli_command(provider_id, executable, prompt, temperature, max_tokens)

        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdin_payload = None if self._command_accepts_inline_prompt(provider_id) else prompt.encode("utf-8")
        stdout, stderr = await asyncio.wait_for(
            process.communicate(stdin_payload),
            timeout=self.timeout_seconds,
        )

        if process.returncode != 0:
            error_text = (stderr or stdout or b"").decode("utf-8", errors="replace").strip()
            raise ProviderCLIExecutionError(
                f"{provider_id} CLI execution failed (exit {process.returncode}): {error_text[:500]}"
            )

        output = (stdout or b"").decode("utf-8", errors="replace").strip()
        if not output:
            output = (stderr or b"").decode("utf-8", errors="replace").strip()
        if not output:
            raise ProviderCLIExecutionError(f"{provider_id} CLI returned no output")

        normalized_output = self._normalize_cli_output(output)
        return ProviderChatResult(
            model=target_model,
            provider_id=provider_id,
            content=normalized_output,
            backend="provider-cli",
            metadata={
                "command": [str(part) for part in command],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "auth_configured": detection.auth_configured,
            },
        )

    def _build_cli_command(
        self,
        provider_id: str,
        executable: Path,
        prompt: str,
        temperature: float,
        max_tokens: Optional[int],
    ) -> List[str]:
        """Best-effort command templates per provider.

        These are intentionally generic. Providers with richer official CLIs may need
        refinement later, but this gives Windows AI a concrete execution path now.
        """
        prompt_arg_map = {
            "gemini": [str(executable), "prompt", prompt],
            "codex": [str(executable), "chat", "--prompt", prompt],
            "claude": [str(executable), "chat", "--prompt", prompt],
            "grok": [str(executable), "chat", "--prompt", prompt],
        }
        stdin_map = {
            "gemini": [str(executable)],
            "codex": [str(executable), "chat"],
            "claude": [str(executable), "chat"],
            "grok": [str(executable), "chat"],
        }

        command = prompt_arg_map.get(provider_id) or stdin_map.get(provider_id)
        if not command:
            raise ProviderCLIExecutionError(f"No command template configured for {provider_id}")

        if max_tokens:
            command += ["--max-tokens", str(max_tokens)]
        if temperature is not None:
            command += ["--temperature", str(temperature)]
        return command

    def _command_accepts_inline_prompt(self, provider_id: str) -> bool:
        return provider_id in {"gemini", "codex", "claude", "grok"}

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        parts: List[str] = []
        for message in messages:
            role = (message.get("role") or "user").upper()
            content = message.get("content") or ""
            parts.append(f"{role}:\n{content}")
        return "\n\n".join(parts).strip()

    def _normalize_cli_output(self, output: str) -> str:
        output = output.strip()
        if not output:
            return output

        try:
            parsed = json.loads(output)
            if isinstance(parsed, dict):
                for key in ("content", "text", "response", "message"):
                    value = parsed.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
                return json.dumps(parsed, indent=2)
        except Exception:
            pass

        return output


provider_cli_executor = ProviderCLIExecutor()
