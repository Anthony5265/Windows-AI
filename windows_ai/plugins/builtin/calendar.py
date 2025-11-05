"""
Calendar Plugin

Manages calendar events, reminders, and schedules.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging

from windows_ai.plugins.base import ToolPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class CalendarPlugin(ToolPlugin):
    """
    Calendar and event management plugin.
    Stores events locally in JSON format.
    """

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            id="calendar",
            name="Calendar",
            description="Manage calendar events, reminders, and schedules",
            version="1.0.0",
            author="Windows AI",
            plugin_type=PluginType.TOOL,
            icon="📅",
            tags=["calendar", "events", "reminders", "scheduling"]
        )

    def __init__(self, metadata: PluginMetadata):
        super().__init__(metadata)
        self.data_dir = Path.home() / ".windows-ai" / "calendar"
        self.events_file = self.data_dir / "events.json"
        self.events: List[Dict[str, Any]] = []

    async def initialize(self) -> bool:
        """Initialize the calendar plugin"""
        # Create data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load existing events
        if self.events_file.exists():
            try:
                with open(self.events_file, 'r') as f:
                    self.events = json.load(f)
                logger.info(f"Loaded {len(self.events)} calendar events")
            except Exception as e:
                logger.error(f"Error loading events: {e}")
                self.events = []
        else:
            self.events = []

        self._initialized = True
        return True

    def _save_events(self):
        """Save events to file"""
        try:
            with open(self.events_file, 'w') as f:
                json.dump(self.events, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving events: {e}")

    async def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a calendar action.

        Actions:
        - create_event: Create a new event
        - list_events: List events (optionally filtered)
        - get_event: Get event by ID
        - update_event: Update an event
        - delete_event: Delete an event
        - get_upcoming: Get upcoming events

        Args:
            query: Action to perform
            parameters: Action parameters
        """
        if not parameters:
            parameters = {}

        action = query.lower()

        try:
            if action == "create_event":
                return await self._create_event(parameters)
            elif action == "list_events":
                return await self._list_events(parameters)
            elif action == "get_event":
                return await self._get_event(parameters)
            elif action == "update_event":
                return await self._update_event(parameters)
            elif action == "delete_event":
                return await self._delete_event(parameters)
            elif action == "get_upcoming":
                return await self._get_upcoming(parameters)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}"
                }

        except Exception as e:
            logger.error(f"Calendar action error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _create_event(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new calendar event"""
        title = params.get("title")
        start_time = params.get("start_time")
        end_time = params.get("end_time")
        description = params.get("description", "")
        location = params.get("location", "")
        reminder = params.get("reminder", None)  # Minutes before event

        if not title or not start_time:
            return {
                "success": False,
                "error": "title and start_time are required"
            }

        # Generate event ID
        event_id = f"event-{len(self.events) + 1}-{int(datetime.now().timestamp())}"

        # Create event
        event = {
            "id": event_id,
            "title": title,
            "start_time": start_time,
            "end_time": end_time or start_time,
            "description": description,
            "location": location,
            "reminder": reminder,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        self.events.append(event)
        self._save_events()

        return {
            "success": True,
            "result": event,
            "message": f"Created event: {title}"
        }

    async def _list_events(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List calendar events"""
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        limit = params.get("limit", 50)

        filtered_events = self.events

        # Filter by date range if provided
        if start_date:
            filtered_events = [
                e for e in filtered_events
                if e["start_time"] >= start_date
            ]

        if end_date:
            filtered_events = [
                e for e in filtered_events
                if e["start_time"] <= end_date
            ]

        # Sort by start time
        filtered_events = sorted(filtered_events, key=lambda x: x["start_time"])

        # Limit results
        filtered_events = filtered_events[:limit]

        return {
            "success": True,
            "result": filtered_events,
            "message": f"Found {len(filtered_events)} events"
        }

    async def _get_event(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific event"""
        event_id = params.get("event_id")

        if not event_id:
            return {
                "success": False,
                "error": "event_id is required"
            }

        for event in self.events:
            if event["id"] == event_id:
                return {
                    "success": True,
                    "result": event
                }

        return {
            "success": False,
            "error": f"Event not found: {event_id}"
        }

    async def _update_event(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an event"""
        event_id = params.get("event_id")

        if not event_id:
            return {
                "success": False,
                "error": "event_id is required"
            }

        for i, event in enumerate(self.events):
            if event["id"] == event_id:
                # Update fields
                for key in ["title", "start_time", "end_time", "description", "location", "reminder"]:
                    if key in params:
                        event[key] = params[key]

                event["updated_at"] = datetime.now().isoformat()
                self.events[i] = event
                self._save_events()

                return {
                    "success": True,
                    "result": event,
                    "message": f"Updated event: {event['title']}"
                }

        return {
            "success": False,
            "error": f"Event not found: {event_id}"
        }

    async def _delete_event(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an event"""
        event_id = params.get("event_id")

        if not event_id:
            return {
                "success": False,
                "error": "event_id is required"
            }

        for i, event in enumerate(self.events):
            if event["id"] == event_id:
                deleted_event = self.events.pop(i)
                self._save_events()

                return {
                    "success": True,
                    "result": deleted_event,
                    "message": f"Deleted event: {deleted_event['title']}"
                }

        return {
            "success": False,
            "error": f"Event not found: {event_id}"
        }

    async def _get_upcoming(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get upcoming events"""
        days = params.get("days", 7)
        limit = params.get("limit", 10)

        now = datetime.now().isoformat()
        future = (datetime.now() + timedelta(days=days)).isoformat()

        upcoming = [
            e for e in self.events
            if now <= e["start_time"] <= future
        ]

        # Sort by start time
        upcoming = sorted(upcoming, key=lambda x: x["start_time"])[:limit]

        return {
            "success": True,
            "result": upcoming,
            "message": f"Found {len(upcoming)} upcoming events in the next {days} days"
        }

    def get_schema(self) -> Dict[str, Any]:
        """Return parameter schema"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "enum": [
                        "create_event", "list_events", "get_event",
                        "update_event", "delete_event", "get_upcoming"
                    ],
                    "description": "Calendar action to perform"
                },
                "parameters": {
                    "type": "object",
                    "description": "Action-specific parameters"
                }
            },
            "required": ["query"]
        }

    def get_function_definition(self) -> Dict[str, Any]:
        """Return OpenAI function definition"""
        return {
            "name": "manage_calendar",
            "description": "Manage calendar events and reminders. Create, list, update, or delete events. Get upcoming events for the next few days.",
            "parameters": self.get_schema()
        }
