from __future__ import annotations

import asyncio
import logging
import os
import shlex
import subprocess
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of a command execution."""
    command: str
    stdout: str
    stderr: str
    return_code: int
    duration_ms: float
    session_id: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def success(self) -> bool:
        return self.return_code == 0


class TerminalSession:
    """An isolated terminal session with its own history and environment."""

    def __init__(self, session_id: str = "", cwd: Optional[str] = None, env: Optional[Dict[str, str]] = None):
        self.session_id = session_id or uuid.uuid4().hex[:12]
        self.cwd = cwd or os.getcwd()
        self.env: Dict[str, str] = dict(os.environ)
        if env:
            self.env.update(env)
        self.history: List[CommandResult] = []
        self.created_at: float = time.time()
        self.max_history: int = 1000

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "cwd": self.cwd,
            "history_count": len(self.history),
            "created_at": self.created_at,
        }


class TerminalEngine:
    """Terminal engine with session management, command history,
    timeout support, and security guards.

    Usage::

        engine = TerminalEngine()
        session = engine.create_session()
        result = engine.run("echo hello", session_id=session.session_id)
        print(result.stdout)  # "hello"

        # Async variant
        result = await engine.run_async("ls -la", timeout=10)
    """

    # Characters blocked in commands for security
    BLOCKED_CHARS = ["|", ">", "<", ";", "&&", "||", "`", "$(",]
    BLOCKED_COMMANDS = ["rm -rf /", "format c:", "mkfs", ":(){", "dd if=/dev"]

    def __init__(self, default_timeout: float = 30.0):
        self.default_timeout = default_timeout
        self.sessions: Dict[str, TerminalSession] = {}
        self.history: List[CommandResult] = []
        self.max_global_history: int = 5000
        self._default_session = TerminalSession(session_id="default")
        self.sessions["default"] = self._default_session

    # ------------------------------------------------------------------ #
    # Session management                                                   #
    # ------------------------------------------------------------------ #

    def create_session(
        self,
        session_id: str = "",
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> TerminalSession:
        """Create a new terminal session."""
        session = TerminalSession(session_id=session_id, cwd=cwd, env=env)
        self.sessions[session.session_id] = session
        logger.info(f"Terminal session created: {session.session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[TerminalSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def close_session(self, session_id: str) -> bool:
        """Close and remove a session."""
        if session_id == "default":
            return False
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Terminal session closed: {session_id}")
            return True
        return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        return [s.to_dict() for s in self.sessions.values()]

    # ------------------------------------------------------------------ #
    # Command execution                                                    #
    # ------------------------------------------------------------------ #

    def _validate_command(self, command: str) -> None:
        """Validate a command against security rules."""
        for char in self.BLOCKED_CHARS:
            if char in command:
                raise ValueError(f"Blocked character/sequence in command: '{char}'")
        cmd_lower = command.lower()
        for blocked in self.BLOCKED_COMMANDS:
            if blocked in cmd_lower:
                raise ValueError(f"Blocked command pattern: '{blocked}'")

    def run(
        self,
        command: str,
        session_id: str = "default",
        timeout: Optional[float] = None,
    ) -> CommandResult:
        """Run a command synchronously in the given session."""
        self._validate_command(command)

        session = self.sessions.get(session_id, self._default_session)
        timeout = timeout or self.default_timeout

        start = time.time()
        try:
            completed = subprocess.run(
                shlex.split(command),
                shell=False,
                capture_output=True,
                text=True,
                check=False,
                cwd=session.cwd,
                env=session.env,
                timeout=timeout,
            )
            result = CommandResult(
                command=command,
                stdout=completed.stdout.strip(),
                stderr=completed.stderr.strip(),
                return_code=completed.returncode,
                duration_ms=round((time.time() - start) * 1000, 2),
                session_id=session.session_id,
            )
        except subprocess.TimeoutExpired:
            result = CommandResult(
                command=command,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                return_code=-1,
                duration_ms=round((time.time() - start) * 1000, 2),
                session_id=session.session_id,
            )

        # Record in history
        session.history.append(result)
        if len(session.history) > session.max_history:
            session.history = session.history[-session.max_history:]

        self.history.append(result)
        if len(self.history) > self.max_global_history:
            self.history = self.history[-self.max_global_history:]

        return result

    async def run_async(
        self,
        command: str,
        session_id: str = "default",
        timeout: Optional[float] = None,
    ) -> CommandResult:
        """Run a command asynchronously."""
        self._validate_command(command)

        session = self.sessions.get(session_id, self._default_session)
        timeout = timeout or self.default_timeout

        start = time.time()
        try:
            process = await asyncio.create_subprocess_exec(
                *shlex.split(command),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=session.cwd,
                env=session.env,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
            result = CommandResult(
                command=command,
                stdout=stdout.decode().strip() if stdout else "",
                stderr=stderr.decode().strip() if stderr else "",
                return_code=process.returncode or 0,
                duration_ms=round((time.time() - start) * 1000, 2),
                session_id=session.session_id,
            )
        except asyncio.TimeoutError:
            process.kill()
            result = CommandResult(
                command=command,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                return_code=-1,
                duration_ms=round((time.time() - start) * 1000, 2),
                session_id=session.session_id,
            )

        session.history.append(result)
        self.history.append(result)
        return result

    # ------------------------------------------------------------------ #
    # History queries                                                      #
    # ------------------------------------------------------------------ #

    def get_history(
        self,
        session_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get command history."""
        if session_id:
            session = self.sessions.get(session_id)
            if not session:
                return []
            entries = session.history[-limit:]
        else:
            entries = self.history[-limit:]
        return [r.to_dict() for r in entries]

    def search_history(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search command history."""
        kw = keyword.lower()
        matches = [r for r in self.history if kw in r.command.lower()]
        return [r.to_dict() for r in matches[-limit:]]

    def clear_history(self, session_id: Optional[str] = None) -> int:
        """Clear command history."""
        if session_id:
            session = self.sessions.get(session_id)
            if session:
                count = len(session.history)
                session.history.clear()
                return count
            return 0
        count = len(self.history)
        self.history.clear()
        for session in self.sessions.values():
            session.history.clear()
        return count

    # ------------------------------------------------------------------ #
    # Status                                                               #
    # ------------------------------------------------------------------ #

    def stats(self) -> Dict[str, Any]:
        """Get terminal engine statistics."""
        return {
            "sessions": len(self.sessions),
            "global_history": len(self.history),
            "default_timeout": self.default_timeout,
        }
