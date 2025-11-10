"""
Sample Test Data
Pre-defined test data for various components
"""

from datetime import datetime
from typing import Dict, Any


def sample_chat_message(
    role: str = "user",
    content: str = "Hello, how can you help me?",
    conversation_id: str = "test-conv-1"
) -> Dict[str, Any]:
    """Generate a sample chat message"""
    return {
        "role": role,
        "content": content,
        "conversation_id": conversation_id,
        "timestamp": datetime.now().isoformat()
    }


def sample_conversation(
    conversation_id: str = "test-conv-1",
    message_count: int = 3
) -> Dict[str, Any]:
    """Generate a sample conversation with multiple messages"""
    messages = []

    for i in range(message_count):
        if i % 2 == 0:
            messages.append(sample_chat_message("user", f"User message {i+1}", conversation_id))
        else:
            messages.append(sample_chat_message("assistant", f"Assistant response {i+1}", conversation_id))

    return {
        "conversation_id": conversation_id,
        "messages": messages,
        "created_at": datetime.now().isoformat()
    }


def sample_plugin_metadata(
    plugin_id: str = "test_plugin",
    enabled: bool = True
) -> Dict[str, Any]:
    """Generate sample plugin metadata"""
    return {
        "id": plugin_id,
        "name": f"Test Plugin {plugin_id}",
        "description": "A test plugin for unit testing",
        "version": "1.0.0",
        "author": "Test Author",
        "plugin_type": "action",
        "enabled": enabled,
        "tags": ["test", "sample"],
        "requirements": [],
        "created_at": datetime.now().isoformat()
    }


def sample_automation(
    automation_id: str = "test-automation-1",
    automation_type: str = "folder_watcher"
) -> Dict[str, Any]:
    """Generate sample automation configuration"""
    if automation_type == "folder_watcher":
        return {
            "id": automation_id,
            "name": "Test Folder Watcher",
            "type": "folder_watcher",
            "config": {
                "path": "/test/path",
                "patterns": ["*.txt", "*.log"],
                "recursive": True,
                "actions": [
                    {
                        "type": "log",
                        "message": "File changed: {file_path}"
                    }
                ]
            },
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }
    elif automation_type == "schedule":
        return {
            "id": automation_id,
            "name": "Test Scheduled Task",
            "type": "schedule",
            "config": {
                "schedule": "*/5 * * * *",  # Every 5 minutes
                "action": {
                    "type": "command",
                    "command": "echo test"
                }
            },
            "enabled": True,
            "created_at": datetime.now().isoformat()
        }
    else:
        raise ValueError(f"Unknown automation type: {automation_type}")


def sample_schedule(
    schedule_id: str = "test-schedule-1",
    schedule_type: str = "cron"
) -> Dict[str, Any]:
    """Generate sample schedule configuration"""
    schedules = {
        "cron": {
            "id": schedule_id,
            "type": "cron",
            "expression": "0 9 * * *",  # Daily at 9 AM
            "timezone": "UTC",
            "action": "test_action"
        },
        "interval": {
            "id": schedule_id,
            "type": "interval",
            "seconds": 300,  # Every 5 minutes
            "action": "test_action"
        },
        "one_time": {
            "id": schedule_id,
            "type": "one_time",
            "timestamp": "2024-12-31T23:59:59Z",
            "action": "test_action"
        }
    }

    return schedules.get(schedule_type, schedules["cron"])


def sample_model_config(
    model_name: str = "test-model",
    model_type: str = "ollama"
) -> Dict[str, Any]:
    """Generate sample model configuration"""
    return {
        "name": model_name,
        "type": model_type,
        "config": {
            "temperature": 0.7,
            "max_tokens": 2000,
            "top_p": 0.9
        },
        "enabled": True
    }


def sample_file_event(
    event_type: str = "created",
    file_path: str = "/test/file.txt"
) -> Dict[str, Any]:
    """Generate sample file system event"""
    return {
        "type": event_type,
        "path": file_path,
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "size": 1024,
            "extension": ".txt"
        }
    }


def sample_api_response(
    success: bool = True,
    data: Any = None
) -> Dict[str, Any]:
    """Generate sample API response"""
    response = {
        "success": success,
        "timestamp": datetime.now().isoformat()
    }

    if success:
        response["data"] = data or {"message": "Operation successful"}
    else:
        response["error"] = "Test error message"

    return response
