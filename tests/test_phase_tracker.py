"""Tests for the Windows AI phase tracking utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from windows_ai.phase_bootstrap import PhaseBootstrapper
from windows_ai.phase_tracker import PhaseTracker
from windows_ai.scheduler import ScheduledTask, EXAMPLE_TASKS


class DummyWatcherManager:
    """Minimal folder watcher manager used for testing."""

    def __init__(self, config_path: Path) -> None:
        self.config_file = config_path
        self.watchers: dict[str, object] = {}
        self.observers: dict[str, object] = {}

    def save_config(self) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            wid: watcher.to_dict() if hasattr(watcher, "to_dict") else watcher
            for wid, watcher in self.watchers.items()
        }
        self.config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_watchers(self):
        return [
            {
                **(watcher.to_dict() if hasattr(watcher, "to_dict") else watcher),
                "running": watcher_id in self.observers,
            }
            for watcher_id, watcher in self.watchers.items()
        ]


class DummyTaskScheduler:
    """Minimal scheduler used for testing."""

    def __init__(self, config_path: Path) -> None:
        self.config_file = config_path
        self.tasks: dict[str, ScheduledTask] = {}

    def save_config(self) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        data = {tid: task.to_dict() for tid, task in self.tasks.items()}
        self.config_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def list_tasks(self):
        return [task.to_dict() for task in self.tasks.values()]


@pytest.fixture()
def phase_tracker(tmp_path: Path) -> PhaseTracker:
    watcher_manager = DummyWatcherManager(tmp_path / "watchers.json")
    scheduler = DummyTaskScheduler(tmp_path / "scheduler.json")

    bootstrapper = PhaseBootstrapper(watcher_manager, scheduler)
    result = bootstrapper.ensure_defaults()

    # Ensure defaults match provided examples
    assert result["watchers_added"] >= 1
    assert result["tasks_added"] == len(EXAMPLE_TASKS)

    repo_root = Path(__file__).resolve().parents[1]
    tracker = PhaseTracker(
        repo_root=repo_root,
        data_dir=tmp_path,
        folder_watcher_manager=watcher_manager,
        task_scheduler=scheduler,
        plugin_dir=repo_root / "windows_ai" / "plugins" / "builtin",
    )
    return tracker


def test_phase_summary_contains_all_phases(phase_tracker: PhaseTracker):
    summary = phase_tracker.get_summary()

    assert "overall_completion" in summary
    assert summary["phases"], "Expected at least one phase in the summary"

    phase_numbers = {phase["phase"] for phase in summary["phases"]}
    assert set(range(0, 10)).issubset(phase_numbers)


def test_phase_two_reports_automation_assets(phase_tracker: PhaseTracker):
    phase_two = phase_tracker.get_phase_status_by_id(2)
    assert phase_two is not None

    metadata = phase_two.metadata
    assert metadata["automation"]["configured"] >= 1
    assert metadata["scheduler"]["configured"] >= 1


def test_phase_tracker_serialization_models(phase_tracker: PhaseTracker):
    phase_one = phase_tracker.get_phase_status_by_id(1)
    assert phase_one is not None

    payload = phase_one.to_dict()
    assert payload["phase"] == 1
    assert payload["completion"] >= 0
    assert isinstance(payload["goals"], list)
    assert all("id" in goal and "completed" in goal for goal in payload["goals"])


def test_phase_five_ecosystem_metrics(phase_tracker: PhaseTracker):
    phase_five = phase_tracker.get_phase_status_by_id(5)
    assert phase_five is not None

    metadata = phase_five.metadata

    assert metadata["plugins"]["count"] >= 5
    assert metadata["plugins"]["registry_ready"]
    assert metadata["plugins"]["loader_ready"]

    assert metadata["ecosystem"]["marketplace"]
    assert metadata["ecosystem"]["marketplace_entry"]
    assert metadata["ecosystem"]["model_discovery"]
    assert metadata["ecosystem"]["discovery_modules"] >= 1

    assert metadata["community"]["community_ready"]
    assert metadata["community"]["docs"].get("CONTRIBUTING.md")


def test_phase_six_capsules_and_policies(phase_tracker: PhaseTracker):
    phase_six = phase_tracker.get_phase_status_by_id(6)
    assert phase_six is not None

    metadata = phase_six.metadata
    assert metadata["capsules"]["workflow_templates"] >= 3
    assert metadata["capsules"]["marketplace_ready"]
    assert metadata["policies"]["documents"] >= 3
    assert metadata["policies"]["engine_ready"]


def test_phase_seven_operations_and_updates(phase_tracker: PhaseTracker):
    phase_seven = phase_tracker.get_phase_status_by_id(7)
    assert phase_seven is not None

    metadata = phase_seven.metadata
    assert metadata["operations"]["watchdog"]["script_ready"]
    assert metadata["operations"]["watchdog"]["docs_ready"]
    assert metadata["updates"]["server_ready"]
    assert metadata["deployment"]["scripts"] >= 6
    assert metadata["operations"]["rollback_ready"]


def test_phase_eight_companion_experiences(phase_tracker: PhaseTracker):
    phase_eight = phase_tracker.get_phase_status_by_id(8)
    assert phase_eight is not None

    metadata = phase_eight.metadata
    assert metadata["experiences"]["mobile_ready"]
    assert metadata["experiences"]["first_run_ready"]
    assert metadata["experiences"]["desktop_wizard_ready"]
    assert metadata["apps"]["portfolio_ready"]
    assert metadata["docs"]["complete"]


def test_phase_nine_developer_platform(phase_tracker: PhaseTracker):
    phase_nine = phase_tracker.get_phase_status_by_id(9)
    assert phase_nine is not None

    metadata = phase_nine.metadata
    assert metadata["sdk"]["language_count"] >= 3
    assert metadata["api"]["exists"]
    assert metadata["distribution"]["agent_ready"]
    assert metadata["docs"]["complete"]
    assert metadata["domains"]["samples_ready"]
