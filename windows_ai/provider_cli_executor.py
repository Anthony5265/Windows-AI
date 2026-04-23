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
            return await self._execute_ollama_chat(target_model, messages, temperature, max_tokens)
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
            async for chunk in self._stream_ollama_chat(target_model, messages, temperature, max_tokens):
                yield chunk
            return

        if target_model.startswith("cli:"):
            provider_id = target_model.split(":", 1)[1]
            async for chunk in self._stream_cli_chat(
                provider_id=provider_id,
                target_model=target_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            ):
                yield chunk
            return

        raise ProviderCLIExecutionError(f"Unsupported provider target: {target_model}")

    async def _execute_ollama_chat(
        self,
        target_model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> ProviderChatResult:
        model_name = target_model.split(":", 1)[1]
        url = f"{self.ollama_base_url}/api/chat"
        payload = self._build_ollama_chat_payload(
            model_name=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
        )

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
                "max_tokens": max_tokens,
            },
        )

    async def _stream_ollama_chat(
        self,
        target_model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> AsyncIterator[str]:
        model_name = target_model.split(":", 1)[1]
        url = f"{self.ollama_base_url}/api/chat"
        payload = self._build_ollama_chat_payload(
            model_name=model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

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

    def _build_ollama_chat_payload(
        self,
        model_name: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
        stream: bool,
    ) -> Dict[str, Any]:
        options: Dict[str, Any] = {
            "temperature": temperature,
        }
        if max_tokens is not None:
            options["num_predict"] = max_tokens

        return {
            "model": model_name,
            "messages": messages,
            "stream": stream,
            "options": options,
        }

    async def _stream_cli_chat(
        self,
        provider_id: str,
        target_model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> AsyncIterator[str]:
        try:
            detection = provider_cli_registry.detect_provider(provider_id)
        except ValueError as exc:
            raise ProviderCLIExecutionError(str(exc)) from exc
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
            yielded_any = False
            stdout_chunks: List[str] = []
            stderr_chunks: List[str] = []
            returncode: Optional[int] = None

            try:
                async for event_type, chunk in self._run_cli_command_stream(
                    command=command,
                    prompt=prompt,
                    inline_prompt=inline_prompt,
                ):
                    if event_type == "stdout":
                        stdout_chunks.append(chunk)
                        normalized = self._normalize_stream_chunk(chunk)
                        if normalized.strip():
                            yielded_any = True
                            yield normalized
                    elif event_type == "stderr":
                        stderr_chunks.append(chunk)
                    elif event_type == "returncode":
                        returncode = int(chunk)
            except asyncio.TimeoutError:
                last_error = f"Timed out after {self.timeout_seconds}s"
                continue
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                last_error = str(exc)
                continue

            if returncode not in (0, None):
                last_error = ("".join(stderr_chunks) or "".join(stdout_chunks) or "").strip() or f"exit {returncode}"
                continue

            if yielded_any:
                return

            combined_output = ("".join(stdout_chunks) or "".join(stderr_chunks)).strip()
            if combined_output:
                normalized_output = self._normalize_cli_output(combined_output)
                if normalized_output:
                    yield normalized_output
                    return

            last_error = "CLI returned no output"

        raise ProviderCLIExecutionError(
            f"{provider_id} CLI streaming failed after {len(command_candidates)} attempt(s): {last_error[:500]}"
        )

    async def _run_cli_command_stream(
        self,
        command: Sequence[str],
        prompt: str,
        inline_prompt: bool,
    ) -> AsyncIterator[Tuple[str, str]]:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        if process.stdin is not None:
            if inline_prompt:
                process.stdin.close()
            else:
                process.stdin.write(prompt.encode("utf-8"))
                await process.stdin.drain()
                process.stdin.close()

        stdout_task = None if process.stdout is None else asyncio.create_task(process.stdout.readline())
        stderr_task = None if process.stderr is None else asyncio.create_task(process.stderr.readline())

        try:
            while stdout_task is not None or stderr_task is not None:
                active_tasks = [task for task in (stdout_task, stderr_task) if task is not None]
                done, _pending = await asyncio.wait(
                    active_tasks,
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=self.timeout_seconds,
                )
                if not done:
                    process.kill()
                    await process.wait()
                    raise asyncio.TimeoutError()

                if stdout_task in done:
                    raw_stdout = stdout_task.result()
                    if raw_stdout:
                        yield ("stdout", raw_stdout.decode("utf-8", errors="replace"))
                        stdout_task = asyncio.create_task(process.stdout.readline()) if process.stdout else None
                    else:
                        stdout_task = None

                if stderr_task in done:
                    raw_stderr = stderr_task.result()
                    if raw_stderr:
                        yield ("stderr", raw_stderr.decode("utf-8", errors="replace"))
                        stderr_task = asyncio.create_task(process.stderr.readline()) if process.stderr else None
                    else:
                        stderr_task = None

            returncode = await asyncio.wait_for(process.wait(), timeout=self.timeout_seconds)
            yield ("returncode", str(returncode))
        finally:
            for task in (stdout_task, stderr_task):
                if task is not None and not task.done():
                    task.cancel()

    async def _execute_cli_chat(
        self,
        provider_id: str,
        target_model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> ProviderChatResult:
        try:
            detection = provider_cli_registry.detect_provider(provider_id)
        except ValueError as exc:
            raise ProviderCLIExecutionError(str(exc)) from exc
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
            variants: List[List[str]] = []
            with_optional_flags = list(command)
            if max_tokens is not None:
                with_optional_flags += ["--max-tokens", str(max_tokens)]
            if temperature is not None:
                with_optional_flags += ["--temperature", str(temperature)]
            variants.append(with_optional_flags)

            if with_optional_flags != list(command):
                variants.append(list(command))

            for cmd in variants:
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

    def _normalize_stream_chunk(self, chunk: str) -> str:
        text = chunk.strip()
        if not text:
            return ""

        parsed_dict = self._parse_json_like_output(text)
        if isinstance(parsed_dict, dict):
            direct = self._extract_text_from_dict(parsed_dict)
            if direct:
                return direct

        return chunk

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
