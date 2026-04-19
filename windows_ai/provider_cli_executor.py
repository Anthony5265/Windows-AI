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
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Tuple
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

    async def execute_chat_stream(
        self,
        target_model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        if target_model.startswith("ollama:"):
            async for chunk in self._stream_ollama_chat(target_model, messages, temperature):
                yield chunk
            return

        result = await self.execute_chat(
            target_model=target_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        if result.content:
            yield result.content

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

    async def _stream_ollama_chat(
        self,
        target_model: str,
        messages: List[Dict[str, str]],
        temperature: float,
    ) -> AsyncIterator[str]:
        model_name = target_model.split(":", 1)[1]
        url = f"{self.ollama_base_url}/api/chat"
        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
            },
        }

        yielded = False
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    chunk = (
                        data.get("message", {}).get("content")
                        or data.get("response")
                        or ""
                    )
                    if chunk:
                        yielded = True
                        yield chunk

        if not yielded:
            raise ProviderCLIExecutionError(f"Ollama streaming returned no output for model {model_name}")

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
        command_candidates = self._build_cli_command_candidates(
            provider_id,
            executable,
            prompt,
            temperature,
            max_tokens,
        )

        last_error = "No provider command attempted"
        for command, inline_prompt in command_candidates:
            try:
                stdout, stderr, returncode = await self._run_cli_command(
                    command=command,
                    prompt=prompt,
                    inline_prompt=inline_prompt,
                )
                if returncode != 0:
                    last_error = (stderr or stdout or "").strip() or f"exit {returncode}"
                    continue

                output = (stdout or "").strip() or (stderr or "").strip()
                if not output:
                    last_error = "CLI returned no output"
                    continue

                normalized_output = self._normalize_cli_output(output)
                if not normalized_output:
                    last_error = "CLI output could not be normalized"
                    continue

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
                        "attempt_count": len(command_candidates),
                    },
                )
            except asyncio.TimeoutError:
                last_error = f"Timed out after {self.timeout_seconds}s"
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                last_error = str(exc)

        raise ProviderCLIExecutionError(
            f"{provider_id} CLI execution failed after {len(command_candidates)} attempt(s): {last_error[:500]}"
        )

    async def _run_cli_command(
        self,
        command: Sequence[str],
        prompt: str,
        inline_prompt: bool,
    ) -> Tuple[str, str, int]:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdin_payload = None if inline_prompt else prompt.encode("utf-8")
        stdout, stderr = await asyncio.wait_for(
            process.communicate(stdin_payload),
            timeout=self.timeout_seconds,
        )
        return (
            (stdout or b"").decode("utf-8", errors="replace"),
            (stderr or b"").decode("utf-8", errors="replace"),
            process.returncode,
        )

    def _build_cli_command_candidates(
        self,
        provider_id: str,
        executable: Path,
        prompt: str,
        temperature: float,
        max_tokens: Optional[int],
    ) -> List[Tuple[List[str], bool]]:
        """Return ordered provider-specific command candidates.

        The first item in the tuple is the command argv list. The second item
        indicates whether the prompt is already included inline and should not be
        sent over stdin.
        """
        exe = str(executable)
        base_candidates: Dict[str, List[Tuple[List[str], bool]]] = {
            "gemini": [
                ([exe, "prompt", prompt], True),
                ([exe, "chat", "--prompt", prompt], True),
                ([exe], False),
            ],
            "codex": [
                ([exe, "chat", "--prompt", prompt], True),
                ([exe, "prompt", prompt], True),
                ([exe, "chat"], False),
                ([exe], False),
            ],
            "claude": [
                ([exe, "chat", "--prompt", prompt], True),
                ([exe, "prompt", prompt], True),
                ([exe, "chat"], False),
                ([exe], False),
            ],
            "grok": [
                ([exe, "chat", "--prompt", prompt], True),
                ([exe, "prompt", prompt], True),
                ([exe, "chat"], False),
                ([exe], False),
            ],
        }

        if provider_id not in base_candidates:
            raise ProviderCLIExecutionError(f"No command template configured for {provider_id}")

        finalized: List[Tuple[List[str], bool]] = []
        seen: set[Tuple[str, ...]] = set()
        for command, inline_prompt in base_candidates[provider_id]:
            cmd = list(command)
            if max_tokens:
                cmd += ["--max-tokens", str(max_tokens)]
            if temperature is not None:
                cmd += ["--temperature", str(temperature)]
            signature = tuple(cmd)
            if signature in seen:
                continue
            seen.add(signature)
            finalized.append((cmd, inline_prompt))
        return finalized

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

        parsed_dict = self._parse_json_like_output(output)
        if isinstance(parsed_dict, dict):
            direct = self._extract_text_from_dict(parsed_dict)
            if direct:
                return direct
            return json.dumps(parsed_dict, indent=2)

        return output

    def _parse_json_like_output(self, output: str) -> Optional[Dict[str, Any]]:
        try:
            parsed = json.loads(output)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            pass

        for line in reversed(output.splitlines()):
            candidate = line.strip()
            if not candidate.startswith("{"):
                continue
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                continue
        return None

    def _extract_text_from_dict(self, parsed: Dict[str, Any]) -> Optional[str]:
        for key in ("content", "text", "response", "message", "output"):
            value = parsed.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
            if isinstance(value, dict):
                nested = self._extract_text_from_dict(value)
                if nested:
                    return nested

        choices = parsed.get("choices")
        if isinstance(choices, list):
            for choice in choices:
                if isinstance(choice, dict):
                    nested = self._extract_text_from_dict(choice)
                    if nested:
                        return nested

        return None


provider_cli_executor = ProviderCLIExecutor()
