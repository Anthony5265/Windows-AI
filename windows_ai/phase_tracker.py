"""Dynamic roadmap tracking for Windows AI phases."""

from __future__ import annotations

import importlib.util
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PhaseGoal:
    """Represents a milestone contributing to a phase."""

    goal_id: str
    description: str
    completed: bool
    evidence: Optional[str] = None
    weight: float = 1.0

    def score(self) -> float:
        return self.weight if self.completed else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.goal_id,
            "description": self.description,
            "completed": self.completed,
            "weight": self.weight,
            "evidence": self.evidence,
        }


@dataclass
class PhaseStatus:
    """Aggregated progress information for a roadmap phase."""

    phase: int
    name: str
    description: str
    goals: List[PhaseGoal] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def completion(self) -> float:
        total_weight = sum(goal.weight for goal in self.goals)
        if not total_weight:
            return 0.0
        score = sum(goal.score() for goal in self.goals)
        return round((score / total_weight) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "name": self.name,
            "description": self.description,
            "completion": self.completion,
            "goals": [goal.to_dict() for goal in self.goals],
            "metadata": self.metadata,
        }


class PhaseTracker:
    """Compute live completion statistics across roadmap phases."""

    def __init__(
        self,
        repo_root: Path,
        data_dir: Optional[Path] = None,
        folder_watcher_manager: Optional[Any] = None,
        task_scheduler: Optional[Any] = None,
        plugin_dir: Optional[Path] = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.docs_root = self.repo_root / "docs"
        self.data_dir = Path(data_dir) if data_dir else Path.home() / ".windows-ai"
        self.folder_watcher_manager = folder_watcher_manager
        self.task_scheduler = task_scheduler
        self.plugin_dir = Path(plugin_dir) if plugin_dir else self.repo_root / "windows_ai" / "plugins" / "builtin"

    # public api ------------------------------------------------------
    def get_phase_statuses(self) -> List[PhaseStatus]:
        watchers = self._get_watchers()
        tasks = self._get_tasks()
        plugin_count = self._count_plugins()

        statuses = [
            self._phase_0_status(),
            self._phase_1_status(plugin_count, watchers, tasks),
            self._phase_2_status(plugin_count, watchers, tasks),
            self._phase_3_status(),
            self._phase_4_status(),
        ]
        return statuses

    def get_phase_status_by_id(self, phase: int) -> Optional[PhaseStatus]:
        for status in self.get_phase_statuses():
            if status.phase == phase:
                return status
        return None

    def get_summary(self) -> Dict[str, Any]:
        statuses = self.get_phase_statuses()
        overall = 0.0
        if statuses:
            overall = round(sum(status.completion for status in statuses) / len(statuses), 2)
        return {
            "overall_completion": overall,
            "phases": [status.to_dict() for status in statuses],
        }

    # phase builders --------------------------------------------------
    def _phase_0_status(self) -> PhaseStatus:
        plan_exists = (self.docs_root / "PLAN.md").exists()
        changelog_exists = (self.repo_root / "CHANGELOG.md").exists()
        security_exists = (self.repo_root / "SECURITY.md").exists()
        rollback_assets = any((self.repo_root / "windows_ai" / "rollback").glob("*.py"))

        goals = [
            PhaseGoal("plan-doc", "Build plan documented", plan_exists, "docs/PLAN.md"),
            PhaseGoal("changelog", "Changelog initialized", changelog_exists, "CHANGELOG.md"),
            PhaseGoal("security", "Security policy documented", security_exists, "SECURITY.md"),
            PhaseGoal("rollback", "Rollback tooling present", rollback_assets, "windows_ai/rollback/"),
        ]

        metadata = {
            "documents": {
                "plan": plan_exists,
                "changelog": changelog_exists,
                "security": security_exists,
            }
        }

        return PhaseStatus(
            phase=0,
            name="Phase 0 — Definition + Safety Net",
            description="Project charter, safety guardrails, and rollback playbooks",
            goals=goals,
            metadata=metadata,
        )

    def _phase_1_status(
        self,
        plugin_count: int,
        watchers: Dict[str, Any],
        tasks: Dict[str, Any],
    ) -> PhaseStatus:
        backend_exists = (self.repo_root / "windows_ai" / "main.py").exists()
        config_exists = (self.data_dir / "config.json").exists()
        watcher_system_ready = watchers["configured"] > 0
        scheduler_ready = tasks["configured"] > 0

        goals = [
            PhaseGoal("backend", "FastAPI core backend available", backend_exists, "windows_ai/main.py"),
            PhaseGoal("config", "User configuration persisted", config_exists, str(self.data_dir / "config.json")),
            PhaseGoal("automation", "Folder automation configured", watcher_system_ready, f"{watchers['configured']} watchers"),
            PhaseGoal("scheduler", "Task scheduler configured", scheduler_ready, f"{tasks['configured']} tasks"),
            PhaseGoal("plugins", "Plugin ecosystem populated", plugin_count > 0, f"{plugin_count} plugins discovered"),
        ]

        metadata = {
            "automation": watchers,
            "scheduler": tasks,
            "plugins": {
                "count": plugin_count,
            },
        }

        return PhaseStatus(
            phase=1,
            name="Phase 1 — Core Agent",
            description="Backend services, automation runtime, and plugin ecosystem",
            goals=goals,
            metadata=metadata,
        )

    def _phase_2_status(
        self,
        plugin_count: int,
        watchers: Dict[str, Any],
        tasks: Dict[str, Any],
    ) -> PhaseStatus:
        gui_exists = (self.repo_root / "apps" / "gui" / "package.json").exists()
        tray_exists = (self.repo_root / "windows-ai-tray").exists()
        automation_templates_ready = watchers["configured"] >= 2
        scheduler_templates_ready = tasks["configured"] >= 2

        goals = [
            PhaseGoal("gui", "Electron GUI present", gui_exists, "apps/gui/package.json"),
            PhaseGoal("tray", "Windows tray application scaffolded", tray_exists, "windows-ai-tray/"),
            PhaseGoal("automation-templates", "Automation templates prepared", automation_templates_ready, f"{watchers['configured']} templates"),
            PhaseGoal("scheduler-templates", "Scheduled automation templates", scheduler_templates_ready, f"{tasks['configured']} templates"),
        ]

        metadata = {
            "ui": {
                "electron_gui": gui_exists,
                "tray": tray_exists,
            },
            "automation": watchers,
            "scheduler": tasks,
            "plugins": {
                "count": plugin_count,
            },
        }

        return PhaseStatus(
            phase=2,
            name="Phase 2 — Tray & GUI Automation",
            description="Desktop UX layers and automation blueprints",
            goals=goals,
            metadata=metadata,
        )

    def _phase_3_status(self) -> PhaseStatus:
        iot_ready = self._module_available("windows_ai.iot") or (self.repo_root / "iot").exists()
        mesh_ready = (self.repo_root / "mesh").exists()
        discovery_ready = (self.repo_root / "model_discovery").exists()
        cloud_ready = (self.repo_root / "cloud_sync").exists()
        search_ready = (self.repo_root / "search").exists()

        goals = [
            PhaseGoal("iot", "IoT integration stack present", iot_ready, "iot/"),
            PhaseGoal("mesh", "Mesh network services ready", mesh_ready, "mesh/"),
            PhaseGoal("discovery", "Model discovery service", discovery_ready, "model_discovery/"),
            PhaseGoal("cloud", "Cloud sync provider", cloud_ready, "cloud_sync/"),
            PhaseGoal("search", "Search index services", search_ready, "search/"),
        ]

        metadata = {
            "integrations": {
                "iot": iot_ready,
                "mesh": mesh_ready,
                "model_discovery": discovery_ready,
                "cloud_sync": cloud_ready,
                "search": search_ready,
            }
        }

        return PhaseStatus(
            phase=3,
            name="Phase 3 — Integrations",
            description="Ecosystem bridges: IoT, mesh networking, discovery, and search",
            goals=goals,
            metadata=metadata,
        )

    def _phase_4_status(self) -> PhaseStatus:
        installer_scripts = (self.repo_root / "installer").exists()
        build_script = (self.repo_root / "build-release.sh").exists()
        watchdog_script = (self.repo_root / "watchdog.py").exists()
        installer_tests = (self.repo_root / "tests" / "installer").exists()

        goals = [
            PhaseGoal("installer", "Windows installer pipeline", installer_scripts, "installer/"),
            PhaseGoal("release", "Release automation scripts", build_script, "build-release.sh"),
            PhaseGoal("watchdog", "Watchdog health service", watchdog_script, "watchdog.py"),
            PhaseGoal("validation", "Installer validation tests", installer_tests, "tests/installer/"),
        ]

        metadata = {
            "packaging": {
                "installer_assets": installer_scripts,
                "release_script": build_script,
                "watchdog": watchdog_script,
                "installer_tests": installer_tests,
            }
        }

        return PhaseStatus(
            phase=4,
            name="Phase 4 — Packaging & Delivery",
            description="Installers, release automation, and validation suites",
            goals=goals,
            metadata=metadata,
        )

    # helpers ---------------------------------------------------------
    def _get_watchers(self) -> Dict[str, Any]:
        manager = self.folder_watcher_manager
        configured = 0
        running = 0

        if manager:
            try:
                listed: Iterable[Dict[str, Any]] = manager.list_watchers()
                listed = list(listed)
                configured = len(listed)
                running = sum(1 for item in listed if item.get("running"))
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Unable to read folder watchers: %s", exc)

        config_path = self.data_dir / "watchers.json"
        return {
            "configured": configured,
            "active": running,
            "config_exists": config_path.exists(),
        }

    def _get_tasks(self) -> Dict[str, Any]:
        scheduler = self.task_scheduler
        configured = 0

        if scheduler:
            try:
                listed: Iterable[Dict[str, Any]] = scheduler.list_tasks()
                configured = len(list(listed))
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Unable to read scheduled tasks: %s", exc)

        config_path = self.data_dir / "scheduler.json"
        return {
            "configured": configured,
            "config_exists": config_path.exists(),
        }

    def _count_plugins(self) -> int:
        try:
            if not self.plugin_dir.exists():
                return 0
            return sum(1 for path in self.plugin_dir.glob("**/*_plugin.py") if path.is_file())
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Unable to count plugins: %s", exc)
            return 0

    @staticmethod
    def _module_available(module_name: str) -> bool:
        try:
            return importlib.util.find_spec(module_name) is not None
        except ModuleNotFoundError:
            return False


__all__ = ["PhaseTracker", "PhaseStatus", "PhaseGoal"]
