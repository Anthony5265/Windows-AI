"""
Opsgenie DevOps Plugin
Supports incident management and alerting through Opsgenie API
"""

from typing import Dict, Any, Optional, List
import os
import requests
import json
from datetime import datetime, timezone


class OpsgeniePlugin:
    """Plugin for Opsgenie API integration"""

    name = "opsgenie"
    version = "1.0.0"
    description = "Integration with Opsgenie API for incident management and alerting"
    author = "Windows AI Team"

    def __init__(self):
        self.api_key: Optional[str] = None
        self.base_url = "https://api.opsgenie.com/v2"
        self.eu_base_url = "https://api.eu.opsgenie.com/v2"
        self.use_eu_region = False
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Opsgenie plugin"""
        try:
            # Get API key from config or environment
            if config:
                self.api_key = config.get("api_key") or os.getenv("OPSGENIE_API_KEY")
                self.use_eu_region = config.get("use_eu_region", False) or os.getenv("OPSGENIE_EU_REGION", "").lower() == "true"
            else:
                self.api_key = os.getenv("OPSGENIE_API_KEY")
                self.use_eu_region = os.getenv("OPSGENIE_EU_REGION", "").lower() == "true"

            if not self.api_key:
                print("No Opsgenie API key provided. Set OPSGENIE_API_KEY environment variable.")
                return False

            # Set base URL based on region
            self.base_url = self.eu_base_url if self.use_eu_region else self.base_url

            # Test connection
            test_result = self._make_request("/account/identifier")
            if "error" in test_result:
                print(f"Opsgenie authentication failed: {test_result['error']}")
                return False

            print(f"Connected to Opsgenie API ({'EU' if self.use_eu_region else 'US'} region)")
            self._initialized = True
            return True

        except Exception as e:
            print(f"Error initializing Opsgenie plugin: {e}")
            return False

    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make request to Opsgenie API"""
        try:
            headers = {
                "Authorization": f"GenieKey {self.api_key}",
                "Content-Type": "application/json"
            }

            url = f"{self.base_url}{endpoint}"

            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=data)
            else:
                return {"error": f"Unsupported HTTP method: {method}"}

            if response.status_code in [200, 201, 202, 204]:
                try:
                    return response.json() if response.content else {}
                except:
                    return {}
            else:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    pass
                return {"error": f"API request failed: {response.status_code} - {response.text}", "details": error_data}

        except Exception as e:
            return {"error": str(e)}

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Opsgenie action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide Opsgenie API key."}

        try:
            if action == "create_alert":
                return self._create_alert(params)
            elif action == "get_alert":
                return self._get_alert(params)
            elif action == "update_alert":
                return self._update_alert(params)
            elif action == "close_alert":
                return self._close_alert(params)
            elif action == "acknowledge_alert":
                return self._acknowledge_alert(params)
            elif action == "snooze_alert":
                return self._snooze_alert(params)
            elif action == "list_alerts":
                return self._list_alerts(params)
            elif action == "delete_alert":
                return self._delete_alert(params)
            elif action == "add_note":
                return self._add_note(params)
            elif action == "create_incident":
                return self._create_incident(params)
            elif action == "get_incident":
                return self._get_incident(params)
            elif action == "update_incident":
                return self._update_incident(params)
            elif action == "close_incident":
                return self._close_incident(params)
            elif action == "list_incidents":
                return self._list_incidents(params)
            elif action == "create_escalation":
                return self._create_escalation(params)
            elif action == "list_escalations":
                return self._list_escalations(params)
            elif action == "get_schedule":
                return self._get_schedule(params)
            elif action == "list_schedules":
                return self._list_schedules(params)
            elif action == "who_is_on_call":
                return self._who_is_on_call(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _create_alert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new alert"""
        message = params.get("message", "")
        alias = params.get("alias", "")
        description = params.get("description", "")
        responders = params.get("responders", [])
        visible_to = params.get("visible_to", [])
        actions = params.get("actions", [])
        tags = params.get("tags", [])
        details = params.get("details", {})
        entity = params.get("entity", "")
        priority = params.get("priority", "P3")  # P1-P5
        source = params.get("source", "Windows AI")

        if not message:
            return {"error": "message is required"}

        data = {
            "message": message,
            "alias": alias,
            "description": description,
            "responders": responders,
            "visibleTo": visible_to,
            "actions": actions,
            "tags": tags,
            "details": details,
            "entity": entity,
            "priority": priority,
            "source": source
        }

        # Remove empty fields
        data = {k: v for k, v in data.items() if v or v == []}

        result = self._make_request("/alerts", "POST", data)

        if "error" in result:
            return result

        return {
            "success": True,
            "alert_id": result.get("alertId"),
            "alias": result.get("alias"),
            "message": message,
            "status": result.get("status"),
            "created_at": result.get("createdAt")
        }

    def _get_alert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific alert"""
        alert_id = params.get("alert_id", "")
        alias = params.get("alias", "")

        if not alert_id and not alias:
            return {"error": "alert_id or alias is required"}

        identifier = alert_id or alias
        query_param = {"identifierType": "id"} if alert_id else {"identifierType": "alias"}

        result = self._make_request(f"/alerts/{identifier}", params=query_param)

        if "error" in result:
            return result

        return {"alert": result}

    def _update_alert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing alert"""
        alert_id = params.get("alert_id", "")
        alias = params.get("alias", "")
        message = params.get("message")
        description = params.get("description")
        tags = params.get("tags")
        details = params.get("details")
        priority = params.get("priority")
        note = params.get("note")

        if not alert_id and not alias:
            return {"error": "alert_id or alias is required"}

        identifier = alert_id or alias
        query_param = {"identifierType": "id"} if alert_id else {"identifierType": "alias"}

        data = {}
        if message is not None:
            data["message"] = message
        if description is not None:
            data["description"] = description
        if tags is not None:
            data["tags"] = tags
        if details is not None:
            data["details"] = details
        if priority is not None:
            data["priority"] = priority
        if note is not None:
            data["note"] = note

        result = self._make_request(f"/alerts/{identifier}", "PATCH", data, query_param)

        if "error" in result:
            return result

        return {"success": True, "message": "Alert updated successfully", "alert": result}

    def _close_alert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close an alert"""
        alert_id = params.get("alert_id", "")
        alias = params.get("alias", "")
        note = params.get("note", "")

        if not alert_id and not alias:
            return {"error": "alert_id or alias is required"}

        identifier = alert_id or alias
        query_param = {"identifierType": "id"} if alert_id else {"identifierType": "alias"}

        data = {"note": note} if note else {}

        result = self._make_request(f"/alerts/{identifier}/close", "POST", data, query_param)

        if "error" in result:
            return result

        return {"success": True, "message": "Alert closed successfully"}

    def _acknowledge_alert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Acknowledge an alert"""
        alert_id = params.get("alert_id", "")
        alias = params.get("alias", "")
        note = params.get("note", "")
        user = params.get("user", "")

        if not alert_id and not alias:
            return {"error": "alert_id or alias is required"}

        identifier = alert_id or alias
        query_param = {"identifierType": "id"} if alert_id else {"identifierType": "alias"}

        data = {"note": note} if note else {}
        if user:
            data["user"] = user

        result = self._make_request(f"/alerts/{identifier}/acknowledge", "POST", data, query_param)

        if "error" in result:
            return result

        return {"success": True, "message": "Alert acknowledged successfully"}

    def _snooze_alert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Snooze an alert"""
        alert_id = params.get("alert_id", "")
        alias = params.get("alias", "")
        minutes = params.get("minutes", 30)
        note = params.get("note", "")

        if not alert_id and not alias:
            return {"error": "alert_id or alias is required"}

        identifier = alert_id or alias
        query_param = {"identifierType": "id"} if alert_id else {"identifierType": "alias"}

        data = {
            "endTime": datetime.now(timezone.utc).timestamp() + (minutes * 60)
        }
        if note:
            data["note"] = note

        result = self._make_request(f"/alerts/{identifier}/snooze", "POST", data, query_param)

        if "error" in result:
            return result

        return {"success": True, "message": f"Alert snoozed for {minutes} minutes"}

    def _list_alerts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List alerts with filtering"""
        query_params = {}
        
        # Add filter parameters
        if params.get("status"):
            query_params["status"] = params["status"]
        if params.get("priority"):
            query_params["priority"] = params["priority"]
        if params.get("limit"):
            query_params["limit"] = min(params["limit"], 100)  # Max 100
        if params.get("offset"):
            query_params["offset"] = params["offset"]
        if params.get("sort"):
            query_params["sort"] = params["sort"]
        if params.get("order"):
            query_params["order"] = params["order"]
        if params.get("search"):
            query_params["search"] = params["search"]
        if params.get("tags"):
            query_params["tags"] = ",".join(params["tags"]) if isinstance(params["tags"], list) else params["tags"]

        result = self._make_request("/alerts", params=query_params)

        if "error" in result:
            return result

        return {
            "alerts": result.get("data", []),
            "paging": result.get("paging", {}),
            "total_count": result.get("totalCount", 0)
        }

    def _delete_alert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete an alert"""
        alert_id = params.get("alert_id", "")
        alias = params.get("alias", "")

        if not alert_id and not alias:
            return {"error": "alert_id or alias is required"}

        identifier = alert_id or alias
        query_param = {"identifierType": "id"} if alert_id else {"identifierType": "alias"}

        result = self._make_request(f"/alerts/{identifier}", "DELETE", params=query_param)

        if "error" in result:
            return result

        return {"success": True, "message": "Alert deleted successfully"}

    def _add_note(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a note to an alert"""
        alert_id = params.get("alert_id", "")
        alias = params.get("alias", "")
        note = params.get("note", "")

        if not alert_id and not alias:
            return {"error": "alert_id or alias is required"}
        if not note:
            return {"error": "note is required"}

        identifier = alert_id or alias
        query_param = {"identifierType": "id"} if alert_id else {"identifierType": "alias"}

        data = {"note": note}

        result = self._make_request(f"/alerts/{identifier}/notes", "POST", data, query_param)

        if "error" in result:
            return result

        return {"success": True, "message": "Note added successfully", "note": result}

    def _create_incident(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new incident"""
        message = params.get("message", "")
        description = params.get("description", "")
        responders = params.get("responders", [])
        tags = params.get("tags", [])
        details = params.get("details", {})
        priority = params.get("priority", "P3")
        source = params.get("source", "Windows AI")
        service_ids = params.get("service_ids", [])

        if not message:
            return {"error": "message is required"}

        data = {
            "message": message,
            "description": description,
            "responders": responders,
            "tags": tags,
            "details": details,
            "priority": priority,
            "source": source,
            "serviceIds": service_ids
        }

        # Remove empty fields
        data = {k: v for k, v in data.items() if v or v == []}

        result = self._make_request("/incidents", "POST", data)

        if "error" in result:
            return result

        return {
            "success": True,
            "incident_id": result.get("id"),
            "message": message,
            "status": result.get("status"),
            "created_at": result.get("createdAt")
        }

    def _get_incident(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific incident"""
        incident_id = params.get("incident_id", "")

        if not incident_id:
            return {"error": "incident_id is required"}

        result = self._make_request(f"/incidents/{incident_id}")

        if "error" in result:
            return result

        return {"incident": result}

    def _update_incident(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing incident"""
        incident_id = params.get("incident_id", "")
        message = params.get("message")
        description = params.get("description")
        tags = params.get("tags")
        details = params.get("details")
        priority = params.get("priority")
        note = params.get("note")

        if not incident_id:
            return {"error": "incident_id is required"}

        data = {}
        if message is not None:
            data["message"] = message
        if description is not None:
            data["description"] = description
        if tags is not None:
            data["tags"] = tags
        if details is not None:
            data["details"] = details
        if priority is not None:
            data["priority"] = priority
        if note is not None:
            data["note"] = note

        result = self._make_request(f"/incidents/{incident_id}", "PATCH", data)

        if "error" in result:
            return result

        return {"success": True, "message": "Incident updated successfully", "incident": result}

    def _close_incident(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Close an incident"""
        incident_id = params.get("incident_id", "")
        note = params.get("note", "")

        if not incident_id:
            return {"error": "incident_id is required"}

        data = {"note": note} if note else {}

        result = self._make_request(f"/incidents/{incident_id}/close", "POST", data)

        if "error" in result:
            return result

        return {"success": True, "message": "Incident closed successfully"}

    def _list_incidents(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List incidents with filtering"""
        query_params = {}
        
        # Add filter parameters
        if params.get("status"):
            query_params["status"] = params["status"]
        if params.get("priority"):
            query_params["priority"] = params["priority"]
        if params.get("limit"):
            query_params["limit"] = min(params["limit"], 100)  # Max 100
        if params.get("offset"):
            query_params["offset"] = params["offset"]
        if params.get("sort"):
            query_params["sort"] = params["sort"]
        if params.get("order"):
            query_params["order"] = params["order"]
        if params.get("search"):
            query_params["search"] = params["search"]
        if params.get("tags"):
            query_params["tags"] = ",".join(params["tags"]) if isinstance(params["tags"], list) else params["tags"]

        result = self._make_request("/incidents", params=query_params)

        if "error" in result:
            return result

        return {
            "incidents": result.get("data", []),
            "paging": result.get("paging", {}),
            "total_count": result.get("totalCount", 0)
        }

    def _create_escalation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an escalation policy"""
        name = params.get("name", "")
        description = params.get("description", "")
        rules = params.get("rules", [])
        owner_team = params.get("owner_team", "")

        if not name:
            return {"error": "name is required"}

        data = {
            "name": name,
            "description": description,
            "rules": rules,
            "ownerTeam": owner_team
        }

        # Remove empty fields
        data = {k: v for k, v in data.items() if v or v == []}

        result = self._make_request("/escalations", "POST", data)

        if "error" in result:
            return result

        return {
            "success": True,
            "escalation_id": result.get("id"),
            "name": name,
            "created_at": result.get("createdAt")
        }

    def _list_escalations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List escalation policies"""
        query_params = {}
        
        if params.get("limit"):
            query_params["limit"] = min(params["limit"], 100)
        if params.get("offset"):
            query_params["offset"] = params["offset"]

        result = self._make_request("/escalations", params=query_params)

        if "error" in result:
            return result

        return {
            "escalations": result.get("data", []),
            "paging": result.get("paging", {}),
            "total_count": result.get("totalCount", 0)
        }

    def _get_schedule(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get a specific schedule"""
        schedule_id = params.get("schedule_id", "")
        schedule_type = params.get("type", "schedule")  # schedule, override

        if not schedule_id:
            return {"error": "schedule_id is required"}

        result = self._make_request(f"/schedules/{schedule_id}")

        if "error" in result:
            return result

        return {"schedule": result}

    def _list_schedules(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List schedules"""
        query_params = {}
        
        if params.get("limit"):
            query_params["limit"] = min(params["limit"], 100)
        if params.get("offset"):
            query_params["offset"] = params["offset"]

        result = self._make_request("/schedules", params=query_params)

        if "error" in result:
            return result

        return {
            "schedules": result.get("data", []),
            "paging": result.get("paging", {}),
            "total_count": result.get("totalCount", 0)
        }

    def _who_is_on_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get who is currently on call"""
        schedule_identifier = params.get("schedule_identifier", "")
        flat = params.get("flat", False)
        date = params.get("date")  # Format: YYYY-MM-DD

        query_params = {"flat": str(flat).lower()}
        if date:
            query_params["date"] = date

        if schedule_identifier:
            result = self._make_request(f"/schedules/{schedule_identifier}/on-calls", params=query_params)
        else:
            result = self._make_request("/schedules/on-calls", params=query_params)

        if "error" in result:
            return result

        return {
            "on_call_data": result.get("data", []),
            "paging": result.get("paging", {}),
            "total_count": result.get("totalCount", 0)
        }

    def cleanup(self):
        """Cleanup resources"""
        self.api_key = None
        self._initialized = False


# Plugin metadata for registration
PLUGIN_CLASS = OpsgeniePlugin
PLUGIN_NAME = "opsgenie"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Opsgenie API for incident management and alerting"
PLUGIN_ACTIONS = [
    "create_alert", "get_alert", "update_alert", "close_alert", "acknowledge_alert",
    "snooze_alert", "list_alerts", "delete_alert", "add_note", "create_incident",
    "get_incident", "update_incident", "close_incident", "list_incidents",
    "create_escalation", "list_escalations", "get_schedule", "list_schedules", "who_is_on_call"
]