# Alert Manager

Allows Windows-AI to define alert rules (predicates evaluated against log
records) and persist/dispatch alert events with optional notification callbacks.

## Usage
```python
from plugins.logging.alert_manager.alert_manager import AlertManager, AlertRule

def notify(alert: dict) -> None:
    print(f\"[{alert['severity']}] {alert['rule']}: {alert['description']}\")

manager = AlertManager(notifier=notify)
manager.register_rule(
    AlertRule(
        name=\"high-error-rate\",
        severity=\"critical\",
        description=\"API produced a high severity error\",
        predicate=lambda record: record.get(\"severity\") == \"high\",
        debounce_seconds=120,
    )
)

manager.evaluate({\"severity\": \"high\", \"message\": \"Failed to call OpenAI\"})
```

Alerts are stored under `logs/alerts/alerts.jsonl` via `JsonLogStore`, making it
easy to triage incidents later.
