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
            self._phase_5_status(plugin_count),
            self._phase_6_status(),
            self._phase_7_status(),
            self._phase_8_status(),
            self._phase_9_status(),
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

    def _phase_5_status(self, plugin_count: int) -> PhaseStatus:
        plugins_root = self.repo_root / "windows_ai" / "plugins"
        registry_ready = (plugins_root / "registry.py").exists()
        loader_ready = (plugins_root / "loader.py").exists()

        marketplace_root = self.repo_root / "marketplace"
        marketplace_ready = marketplace_root.exists()
        marketplace_entry = (marketplace_root / "main.py").exists()

        model_discovery_root = self.repo_root / "model_discovery"
        model_discovery_ready = model_discovery_root.exists()
        discovery_modules = 0
        if model_discovery_ready:
            discovery_modules = sum(
                1
                for path in model_discovery_root.glob("*.py")
                if path.is_file()
            )

        community_docs = [
            self.repo_root / "CONTRIBUTING.md",
            self.repo_root / "CHANGELOG.md",
            self.docs_root / "ROADMAP.md",
            self.docs_root / "ROADMAP_IMPLEMENTATION.md",
        ]
        community_status: Dict[str, bool] = {}
        for doc_path in community_docs:
            try:
                key = str(doc_path.relative_to(self.repo_root))
            except ValueError:  # pragma: no cover - defensive safety
                key = str(doc_path)
            community_status[key] = doc_path.exists()

        community_ready = all(community_status.values())

        plugin_catalog_ready = plugin_count >= 5

        goals = [
            PhaseGoal(
                "plugin-catalog",
                "Plugin catalog populated",
                plugin_catalog_ready,
                f"{plugin_count} plugins discovered",
            ),
            PhaseGoal(
                "plugin-registry",
                "Plugin registry operational",
                registry_ready and loader_ready,
                "windows_ai/plugins/",
            ),
            PhaseGoal(
                "model-discovery",
                "Model discovery service available",
                model_discovery_ready and discovery_modules >= 2,
                f"{discovery_modules} discovery modules",
            ),
            PhaseGoal(
                "marketplace",
                "Marketplace tooling ready",
                marketplace_ready and marketplace_entry,
                "marketplace/main.py",
            ),
            PhaseGoal(
                "community",
                "Community guides published",
                community_ready,
                ", ".join(sorted(community_status.keys())),
            ),
        ]

        metadata = {
            "plugins": {
                "count": plugin_count,
                "registry_ready": registry_ready,
                "loader_ready": loader_ready,
                "catalog_path": str(self.plugin_dir),
            },
            "ecosystem": {
                "marketplace": marketplace_ready,
                "marketplace_entry": marketplace_entry,
                "model_discovery": model_discovery_ready,
                "discovery_modules": discovery_modules,
            },
            "community": {
                "docs": community_status,
                "community_ready": community_ready,
            },
        }

        return PhaseStatus(
            phase=5,
            name="Phase 5 — Ecosystem & Growth",
            description="Plugin marketplace, model discovery, and community enablement",
            goals=goals,
            metadata=metadata,
        )

    def _phase_6_status(self) -> PhaseStatus:
        control_center_dir = self.repo_root / "control_center"
        ui_modules = 0
        if control_center_dir.exists():
            ui_modules = sum(1 for path in control_center_dir.glob("*.py") if path.is_file())

        workflow_dir = self.repo_root / "assets" / "workflows"
        workflow_templates = 0
        if workflow_dir.exists():
            workflow_templates = sum(1 for path in workflow_dir.rglob("*.yaml"))

        marketplace_root = self.repo_root / "marketplace"
        marketplace_entry = marketplace_root / "main.py"
        marketplace_ready = marketplace_root.exists() and marketplace_entry.exists()

        policy_docs = [
            self.repo_root / "SECURITY.md",
            self.docs_root / "security.md",
            self.docs_root / "security_privacy.md",
            self.docs_root / "SECURITY_ENCRYPTION.md",
        ]
        policy_document_status: Dict[str, bool] = {}
        for doc in policy_docs:
            try:
                key = str(doc.relative_to(self.repo_root))
            except ValueError:  # pragma: no cover - defensive safety
                key = str(doc)
            policy_document_status[key] = doc.exists()
        policy_document_count = sum(1 for present in policy_document_status.values() if present)

        permissions_module = self.repo_root / "security" / "permissions.py"
        audit_module = self.repo_root / "security" / "audit.py"
        policy_engine_ready = permissions_module.exists() and audit_module.exists()

        workflow_threshold_met = workflow_templates >= 3
        ui_threshold_met = ui_modules >= 5
        catalog_ready = workflow_threshold_met and ui_threshold_met and marketplace_ready

        goals = [
            PhaseGoal(
                "capsule-ui",
                "Control Center capsules and marketplace surfaces",
                ui_threshold_met,
                f"{ui_modules} UI modules in control_center/",
            ),
            PhaseGoal(
                "capsule-templates",
                "Workflow capsules curated",
                workflow_threshold_met,
                f"{workflow_templates} workflow templates",
            ),
            PhaseGoal(
                "marketplace-surface",
                "Marketplace entry + UI stitched",
                marketplace_ready,
                str(marketplace_entry),
            ),
            PhaseGoal(
                "policy-docs",
                "Security and governance policies published",
                policy_document_count >= 3,
                ", ".join(sorted(policy_document_status.keys())),
            ),
            PhaseGoal(
                "policy-engine",
                "Policy enforcement engine wired up",
                policy_engine_ready,
                "security/permissions.py, security/audit.py",
            ),
        ]

        metadata = {
            "capsules": {
                "ui_modules": ui_modules,
                "workflow_templates": workflow_templates,
                "marketplace_ready": marketplace_ready,
                "catalog_ready": catalog_ready,
            },
            "policies": {
                "documents": policy_document_count,
                "document_status": policy_document_status,
                "engine_ready": policy_engine_ready,
                "permissions_module": str(permissions_module),
                "audit_module": str(audit_module),
            },
        }

        return PhaseStatus(
            phase=6,
            name="Phase 6 — Capsules & Policy Governance",
            description="Capsule storefront, curated templates, and policy guardrails",
            goals=goals,
            metadata=metadata,
        )

    def _phase_7_status(self) -> PhaseStatus:
        watchdog_script = self.repo_root / "watchdog.py"
        watchdog_docs = self.docs_root / "WATCHDOG.md"
        watchdog_docs_ready = watchdog_docs.exists()
        watchdog_ready = watchdog_script.exists()

        update_server = self.repo_root / "update-server" / "server.py"
        update_manifest = self.repo_root / "update-server" / "manifest.json"
        update_server_ready = update_server.exists() and update_manifest.exists()

        deployment_scripts = [
            path
            for path in self.repo_root.glob("start-*.*")
            if path.suffix.lower() in {".sh", ".bat", ".ps1"}
        ]
        deployment_script_count = len(deployment_scripts)
        deployment_scripts_ready = deployment_script_count >= 6

        updates_docs = [
            self.docs_root / "updates.md",
            self.docs_root / "Smart-Installer.md",
            self.docs_root / "uninstall.md",
        ]
        updates_documentation_ready = all(doc.exists() for doc in updates_docs)

        rollback_module = self.repo_root / "security" / "rollback.py"
        rollback_docs = self.docs_root / "rollback.md"
        rollback_ready = rollback_module.exists() and rollback_docs.exists()

        goals = [
            PhaseGoal(
                "watchdog",
                "Watchdog self-healing service",
                watchdog_ready and watchdog_docs_ready,
                f"watchdog.py + {watchdog_docs.name}",
            ),
            PhaseGoal(
                "update-server",
                "Update server deployment assets",
                update_server_ready,
                "update-server/server.py",
            ),
            PhaseGoal(
                "deploy-scripts",
                "Cross-platform deployment scripts",
                deployment_scripts_ready,
                f"{deployment_script_count} start-* scripts",
            ),
            PhaseGoal(
                "update-docs",
                "Update + uninstall runbooks",
                updates_documentation_ready,
                ", ".join(doc.name for doc in updates_docs),
            ),
            PhaseGoal(
                "rollback-automation",
                "Rollback + recovery automation",
                rollback_ready,
                f"{rollback_module} + {rollback_docs}",
            ),
        ]

        metadata = {
            "operations": {
                "watchdog": {
                    "script_ready": watchdog_ready,
                    "docs_ready": watchdog_docs_ready,
                },
                "rollback_ready": rollback_ready,
            },
            "updates": {
                "server_ready": update_server_ready,
                "manifest": str(update_manifest),
                "documentation_ready": updates_documentation_ready,
            },
            "deployment": {
                "scripts": deployment_script_count,
                "scripts_ready": deployment_scripts_ready,
            },
        }

        return PhaseStatus(
            phase=7,
            name="Phase 7 — Operations & Extreme Hardening",
            description="Watchdog, updates, and recovery automation for production scale",
            goals=goals,
            metadata=metadata,
        )

    def _phase_8_status(self) -> PhaseStatus:
        mobile_app = self.repo_root / "mobile" / "package.json"
        first_run_wizard = self.repo_root / "first-run-wizard" / "wizard.html"
        desktop_wizard = self.repo_root / "wizard" / "wizard.html"

        apps_root = self.repo_root / "apps"
        app_projects = []
        if apps_root.exists():
            for package_file in apps_root.glob("*/package.json"):
                if package_file.is_file():
                    app_projects.append(package_file.parent.name)
        app_project_count = len(app_projects)
        portfolio_ready = app_project_count >= 3

        experience_docs = [
            self.docs_root / "AI-Control-Center.md",
            self.docs_root / "AUTOMATION_UI.md",
            self.docs_root / "ACTIONS_API.md",
        ]
        doc_status: Dict[str, bool] = {}
        for doc in experience_docs:
            try:
                key = str(doc.relative_to(self.repo_root))
            except ValueError:  # pragma: no cover - defensive safety
                key = str(doc)
            doc_status[key] = doc.exists()
        docs_ready = all(doc_status.values()) and len(doc_status) >= 3

        goals = [
            PhaseGoal(
                "mobile-companion",
                "Mobile companion experience",
                mobile_app.exists(),
                str(mobile_app),
            ),
            PhaseGoal(
                "first-run-wizard",
                "First-run wizard onboarding",
                first_run_wizard.exists(),
                str(first_run_wizard),
            ),
            PhaseGoal(
                "desktop-onboarding",
                "Desktop setup wizard",
                desktop_wizard.exists(),
                str(desktop_wizard),
            ),
            PhaseGoal(
                "app-portfolio",
                "Desktop and service app portfolio",
                portfolio_ready,
                f"{app_project_count} Electron/Node app projects",
            ),
            PhaseGoal(
                "experience-docs",
                "Cross-surface documentation",
                docs_ready,
                ", ".join(sorted(doc_status.keys())),
            ),
        ]

        metadata = {
            "experiences": {
                "mobile_ready": mobile_app.exists(),
                "first_run_ready": first_run_wizard.exists(),
                "desktop_wizard_ready": desktop_wizard.exists(),
            },
            "apps": {
                "projects": app_projects,
                "portfolio_ready": portfolio_ready,
            },
            "docs": {
                "coverage": doc_status,
                "complete": docs_ready,
            },
        }

        return PhaseStatus(
            phase=8,
            name="Phase 8 — Companion Surfaces & Onboarding",
            description="Mobile, desktop wizards, and multi-app experiences",
            goals=goals,
            metadata=metadata,
        )

    def _phase_9_status(self) -> PhaseStatus:
        sdk_root = self.repo_root / "sdk"
        sdk_languages: Dict[str, bool] = {}
        if sdk_root.exists():
            for child in sdk_root.iterdir():
                if not child.is_dir():
                    continue
                has_assets = any(child.glob("*.py")) or any(child.glob("*.js")) or any(
                    child.glob("*.ts")
                )
                sdk_languages[child.name] = has_assets
        sdk_language_count = sum(1 for ready in sdk_languages.values() if ready)

        openapi_spec = self.repo_root / "openapi" / "windows-ai.yaml"

        agent_dir = self.repo_root / "windows-ai-agent"
        agent_package = agent_dir / "package.json"
        agent_bin = agent_dir / "bin"
        agent_ready = agent_package.exists() and agent_bin.exists()

        developer_docs = [
            self.docs_root / "API_REFERENCE.md",
            self.docs_root / "ACTIONS_API.md",
            self.docs_root / "ENHANCEMENTS_SUMMARY.md",
        ]
        developer_doc_status: Dict[str, bool] = {}
        for doc in developer_docs:
            try:
                key = str(doc.relative_to(self.repo_root))
            except ValueError:  # pragma: no cover - defensive safety
                key = str(doc)
            developer_doc_status[key] = doc.exists()
        developer_doc_ready = all(developer_doc_status.values())

        domains_root = self.repo_root / "domains"
        domain_samples = []
        if domains_root.exists():
            for module in domains_root.glob("*.py"):
                if module.name == "__init__.py" or not module.is_file():
                    continue
                domain_samples.append(module.name)
        domain_samples_ready = len(domain_samples) >= 3

        goals = [
            PhaseGoal(
                "sdk-languages",
                "Multi-language SDK coverage",
                sdk_language_count >= 3,
                f"{sdk_language_count} SDK languages",
            ),
            PhaseGoal(
                "openapi-spec",
                "OpenAPI contract published",
                openapi_spec.exists(),
                str(openapi_spec),
            ),
            PhaseGoal(
                "cli-agent",
                "Agent CLI distribution",
                agent_ready,
                str(agent_dir),
            ),
            PhaseGoal(
                "developer-docs",
                "Developer reference documentation",
                developer_doc_ready,
                ", ".join(sorted(developer_doc_status.keys())),
            ),
            PhaseGoal(
                "domain-samples",
                "Reference domain samples",
                domain_samples_ready,
                ", ".join(sorted(domain_samples)),
            ),
        ]

        metadata = {
            "sdk": {
                "languages": sdk_languages,
                "language_count": sdk_language_count,
            },
            "api": {
                "openapi_spec": str(openapi_spec),
                "exists": openapi_spec.exists(),
            },
            "distribution": {
                "agent_ready": agent_ready,
                "package_json": str(agent_package),
                "bin_path": str(agent_bin),
            },
            "docs": {
                "coverage": developer_doc_status,
                "complete": developer_doc_ready,
            },
            "domains": {
                "samples": domain_samples,
                "samples_ready": domain_samples_ready,
            },
        }

        return PhaseStatus(
            phase=9,
            name="Phase 9 — Developer Platform & Distribution",
            description="SDK coverage, contracts, and CLI packaging",
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
