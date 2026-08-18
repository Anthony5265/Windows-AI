"""Framework-neutral adaptive UI specification generator."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveUiGeneratorResult:
    result_id: str
    status: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AdaptiveUiGenerator:
    """Generate a portable UI specification from a task description.

    The output deliberately avoids committing Windows AI to a specific UI
    framework. Consumers can translate the specification to WinUI, web, or
    another presentation layer.
    """

    STATE_FILENAME = "adaptive_ui_generator_state.json"

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[AdaptiveUiGeneratorResult] = []
        self._load_state()
        logger.info("AdaptiveUiGenerator initialized")

    @staticmethod
    def _build_spec(input_data: Dict[str, Any]) -> Dict[str, Any]:
        title = str(input_data.get("title") or input_data.get("task") or "Windows AI")
        description = input_data.get("description")
        fields = input_data.get("fields", [])
        if fields is None:
            fields = []
        if not isinstance(fields, list):
            raise TypeError("fields must be a list")

        controls: List[Dict[str, Any]] = []
        for index, field_spec in enumerate(fields):
            if isinstance(field_spec, str):
                field_spec = {"name": field_spec}
            if not isinstance(field_spec, dict):
                raise TypeError(f"fields[{index}] must be a string or object")
            name = str(field_spec.get("name") or field_spec.get("id") or f"field_{index + 1}")
            control_type = str(field_spec.get("type", "text")).lower()
            allowed = {"text", "number", "email", "password", "checkbox", "select", "textarea", "button"}
            if control_type not in allowed:
                control_type = "text"
            control: Dict[str, Any] = {
                "id": name,
                "type": control_type,
                "label": str(field_spec.get("label") or name.replace("_", " ").title()),
            }
            if "required" in field_spec:
                control["required"] = bool(field_spec["required"])
            if control_type == "select":
                options = field_spec.get("options", [])
                if not isinstance(options, list):
                    raise TypeError(f"options for {name} must be a list")
                control["options"] = [str(option) for option in options]
            if "default" in field_spec:
                control["default"] = field_spec["default"]
            controls.append(control)

        return {
            "version": 1,
            "title": title,
            "description": str(description) if description is not None else None,
            "layout": str(input_data.get("layout", "stack")),
            "controls": controls,
            "actions": input_data.get("actions", []),
        }

    def process(self, input_data: Dict[str, Any]) -> AdaptiveUiGeneratorResult:
        if not isinstance(input_data, dict):
            raise TypeError("input_data must be a dictionary")
        spec = self._build_spec(input_data)
        result = AdaptiveUiGeneratorResult(
            result_id=str(uuid.uuid4()),
            status="success",
            data={"processed": True, "ui_spec": spec},
        )
        self.results.append(result)
        self._save_state()
        logger.info("Generated adaptive UI specification")
        return result

    def get_results(self) -> List[AdaptiveUiGeneratorResult]:
        return list(self.results)

    @property
    def state_path(self) -> Path:
        return self.data_dir / self.STATE_FILENAME

    def _save_state(self) -> None:
        payload = {
            "version": 1,
            "results": [
                {**asdict(result), "timestamp": result.timestamp.isoformat()}
                for result in self.results
            ],
        }
        temporary = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        try:
            temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            temporary.replace(self.state_path)
        except OSError:
            logger.exception("Failed to save adaptive UI generator state")
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    def _load_state(self) -> None:
        try:
            if not self.state_path.exists():
                return
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("results", []), list):
                raise ValueError("invalid adaptive UI state format")
            loaded: List[AdaptiveUiGeneratorResult] = []
            for item in payload["results"]:
                if not isinstance(item, dict) or "result_id" not in item:
                    continue
                timestamp = datetime.fromisoformat(item["timestamp"]) if item.get("timestamp") else datetime.now(timezone.utc)
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)
                loaded.append(AdaptiveUiGeneratorResult(
                    result_id=str(item["result_id"]),
                    status=str(item.get("status", "success")),
                    data=dict(item.get("data", {})),
                    timestamp=timestamp,
                ))
            self.results = loaded
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            logger.exception("Failed to load adaptive UI generator state")
            self.results = []


_adaptive_ui_generator: Optional[AdaptiveUiGenerator] = None


def get_adaptive_ui_generator() -> Optional[AdaptiveUiGenerator]:
    return _adaptive_ui_generator


def initialize_adaptive_ui_generator(data_dir: Path) -> AdaptiveUiGenerator:
    global _adaptive_ui_generator
    _adaptive_ui_generator = AdaptiveUiGenerator(data_dir)
    return _adaptive_ui_generator
