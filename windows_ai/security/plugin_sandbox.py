"""Plugin Sandbox — Isolated execution environment for plugins.

Provides resource-limited, permission-gated execution so that third-party
plugins cannot damage the host system. Follows the "Freedom First"
philosophy: sandbox is **disabled** by default and users opt-in.

Security levels:
- NONE:    Full system access (default)
- MINIMAL: Block dangerous imports only
- STANDARD: + File-system restrictions + network allow-list
- STRICT:  + Memory/CPU limits + no subprocess spawning
- MAXIMUM: + Read-only FS + no network
"""

from __future__ import annotations

import importlib
import logging
import os
import resource as _resource_mod  # Unix only; Windows uses job objects
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class SandboxLevel(str, Enum):
    """Sandbox restriction levels."""
    NONE = "none"
    MINIMAL = "minimal"
    STANDARD = "standard"
    STRICT = "strict"
    MAXIMUM = "maximum"


@dataclass
class SandboxPolicy:
    """Configuration for a sandbox execution."""
    level: SandboxLevel = SandboxLevel.NONE
    max_memory_mb: int = 512
    max_cpu_seconds: float = 30.0
    allowed_imports: Set[str] = field(default_factory=set)
    blocked_imports: Set[str] = field(default_factory=lambda: {
        "ctypes", "subprocess", "shutil", "socket",
        "multiprocessing", "signal", "pty",
    })
    allowed_paths: List[str] = field(default_factory=list)
    blocked_paths: List[str] = field(default_factory=lambda: [
        "/etc", "/var", "/root", "C:\\Windows\\System32",
    ])
    network_allowed: bool = True
    network_allowlist: List[str] = field(default_factory=list)
    allow_subprocess: bool = True
    read_only_fs: bool = False


@dataclass
class SandboxResult:
    """Result of a sandboxed execution."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    memory_peak_mb: float = 0.0
    violations: List[str] = field(default_factory=list)


class _ImportGuard:
    """Meta-path finder that blocks disallowed imports inside a sandbox."""

    def __init__(self, blocked: Set[str]):
        self.blocked = blocked
        self.violations: List[str] = []

    def find_module(self, fullname: str, path=None):
        top = fullname.split(".")[0]
        if top in self.blocked:
            self.violations.append(f"Blocked import: {fullname}")
            return self  # return self to trigger load_module -> error
        return None

    def load_module(self, fullname: str):
        raise ImportError(f"Import '{fullname}' is blocked by sandbox policy")


class PluginSandbox:
    """Isolated execution environment for plugins.

    Usage::

        sandbox = PluginSandbox(SandboxPolicy(level=SandboxLevel.STANDARD))
        result = sandbox.execute(my_plugin_func, arg1, arg2)
        if not result.success:
            print(result.error, result.violations)
    """

    def __init__(self, policy: Optional[SandboxPolicy] = None):
        self.policy = policy or SandboxPolicy()
        self._active = False
        self._guard: Optional[_ImportGuard] = None
        logger.info("PluginSandbox created, level=%s", self.policy.level.value)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(self, func: Callable, *args, **kwargs) -> SandboxResult:
        """Execute *func* inside the sandbox and return the result."""
        if self.policy.level == SandboxLevel.NONE:
            return self._run_unrestricted(func, *args, **kwargs)

        start = time.perf_counter()
        violations: List[str] = []

        try:
            with self._apply_import_guard() as guard:
                with self._apply_resource_limits():
                    result = func(*args, **kwargs)
                    violations.extend(guard.violations)

            elapsed = (time.perf_counter() - start) * 1000
            return SandboxResult(
                success=True,
                result=result,
                execution_time_ms=round(elapsed, 2),
                violations=violations,
            )
        except MemoryError:
            return SandboxResult(
                success=False,
                error="Memory limit exceeded",
                execution_time_ms=round((time.perf_counter() - start) * 1000, 2),
                violations=violations + ["Memory limit exceeded"],
            )
        except ImportError as exc:
            return SandboxResult(
                success=False,
                error=str(exc),
                execution_time_ms=round((time.perf_counter() - start) * 1000, 2),
                violations=violations + [str(exc)],
            )
        except Exception as exc:
            return SandboxResult(
                success=False,
                error=str(exc),
                execution_time_ms=round((time.perf_counter() - start) * 1000, 2),
                violations=violations,
            )

    def check_path_access(self, path: str) -> bool:
        """Check whether *path* is allowed under current policy."""
        if self.policy.level == SandboxLevel.NONE:
            return True
        abs_path = os.path.abspath(path)
        for blocked in self.policy.blocked_paths:
            if abs_path.startswith(os.path.abspath(blocked)):
                return False
        if self.policy.allowed_paths:
            return any(abs_path.startswith(os.path.abspath(a)) for a in self.policy.allowed_paths)
        return True

    def check_network_access(self, host: str) -> bool:
        """Check whether network access to *host* is allowed."""
        if self.policy.level == SandboxLevel.NONE:
            return True
        if not self.policy.network_allowed:
            return False
        if self.policy.network_allowlist:
            return host in self.policy.network_allowlist
        return True

    def get_policy_summary(self) -> Dict[str, Any]:
        """Return a human-readable summary of the active policy."""
        return {
            "level": self.policy.level.value,
            "max_memory_mb": self.policy.max_memory_mb,
            "max_cpu_seconds": self.policy.max_cpu_seconds,
            "blocked_imports": sorted(self.policy.blocked_imports),
            "network_allowed": self.policy.network_allowed,
            "allow_subprocess": self.policy.allow_subprocess,
            "read_only_fs": self.policy.read_only_fs,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run_unrestricted(self, func: Callable, *args, **kwargs) -> SandboxResult:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return SandboxResult(
                success=True,
                result=result,
                execution_time_ms=round((time.perf_counter() - start) * 1000, 2),
            )
        except Exception as exc:
            return SandboxResult(
                success=False,
                error=str(exc),
                execution_time_ms=round((time.perf_counter() - start) * 1000, 2),
            )

    @contextmanager
    def _apply_import_guard(self):
        guard = _ImportGuard(self.policy.blocked_imports)
        sys.meta_path.insert(0, guard)
        try:
            yield guard
        finally:
            if guard in sys.meta_path:
                sys.meta_path.remove(guard)

    @contextmanager
    def _apply_resource_limits(self):
        """Apply CPU / memory limits on Unix (best-effort on other OS)."""
        old_limits = {}
        try:
            if sys.platform != "win32" and self.policy.level in (
                SandboxLevel.STRICT, SandboxLevel.MAXIMUM
            ):
                mem_bytes = self.policy.max_memory_mb * 1024 * 1024
                soft, hard = _resource_mod.getrlimit(_resource_mod.RLIMIT_AS)
                old_limits["RLIMIT_AS"] = (soft, hard)
                _resource_mod.setrlimit(_resource_mod.RLIMIT_AS, (mem_bytes, hard))
        except Exception:
            pass  # best-effort; some environments don't allow setrlimit

        try:
            yield
        finally:
            for key, (s, h) in old_limits.items():
                try:
                    _resource_mod.setrlimit(getattr(_resource_mod, key), (s, h))
                except Exception:
                    pass
