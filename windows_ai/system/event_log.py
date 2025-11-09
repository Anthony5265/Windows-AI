"""
Windows Event Log Module
Read and analyze Windows event logs
"""
from typing import Dict, Any, List, Optional
import logging
import platform
import subprocess

logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == "Windows"

# Try to import Windows-specific modules
if IS_WINDOWS:
    try:
        import win32evtlog
        import win32evtlogutil
        import win32con
        PYWIN32_AVAILABLE = True
    except ImportError:
        PYWIN32_AVAILABLE = False
        logger.warning("pywin32 not available. Install with: pip install pywin32")
else:
    PYWIN32_AVAILABLE = False


class EventLogManager:
    """Production Windows Event Log access"""

    def __init__(self):
        self.is_available = PYWIN32_AVAILABLE

        if self.is_available:
            # Event types
            self.event_types = {
                win32con.EVENTLOG_ERROR_TYPE: "Error",
                win32con.EVENTLOG_WARNING_TYPE: "Warning",
                win32con.EVENTLOG_INFORMATION_TYPE: "Information",
                win32con.EVENTLOG_AUDIT_SUCCESS: "Audit Success",
                win32con.EVENTLOG_AUDIT_FAILURE: "Audit Failure"
            }
        else:
            self.event_types = {}

    def read_events(self, log_name: str = "System", max_events: int = 100,
                    event_type: str = None) -> Dict[str, Any]:
        """
        Read events from Windows event log

        Args:
            log_name: Name of log (System, Application, Security, etc.)
            max_events: Maximum number of events to retrieve
            event_type: Filter by event type (Error, Warning, Information)

        Returns:
            Dict with event list
        """
        if not self.is_available:
            # Fallback to PowerShell
            return self._read_events_powershell(log_name, max_events, event_type)

        try:
            hand = win32evtlog.OpenEventLog(None, log_name)
            flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ

            events = []
            event_count = 0

            while event_count < max_events:
                events_read = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events_read:
                    break

                for event in events_read:
                    if event_count >= max_events:
                        break

                    event_type_name = self.event_types.get(event.EventType, "Unknown")

                    # Apply filter if specified
                    if event_type and event_type_name.lower() != event_type.lower():
                        continue

                    # Get event description
                    try:
                        description = win32evtlogutil.SafeFormatMessage(event, log_name)
                    except Exception:
                        description = "Unable to format message"

                    events.append({
                        "time_generated": str(event.TimeGenerated),
                        "event_id": event.EventID & 0xFFFF,  # Lower 16 bits
                        "event_type": event_type_name,
                        "source": event.SourceName,
                        "computer": event.ComputerName,
                        "description": description,
                        "category": event.EventCategory
                    })

                    event_count += 1

            win32evtlog.CloseEventLog(hand)

            return {
                "status": "success",
                "log_name": log_name,
                "events": events,
                "count": len(events)
            }

        except Exception as e:
            logger.error(f"Event log read error: {e}")
            return {"status": "error", "message": str(e)}

    def _read_events_powershell(self, log_name: str, max_events: int,
                                event_type: str = None) -> Dict[str, Any]:
        """Fallback to PowerShell for reading event logs"""
        if not IS_WINDOWS:
            return {
                "status": "error",
                "message": "Event log access not available (not Windows)"
            }

        try:
            # Build PowerShell command
            ps_filter = ""
            if event_type:
                ps_filter = f" | Where-Object {{$_.EntryType -eq '{event_type}'}}"

            command = f'Get-EventLog -LogName "{log_name}" -Newest {max_events}{ps_filter} | Select-Object TimeGenerated, EntryType, Source, EventID, Message | ConvertTo-Json'

            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": f"PowerShell error: {result.stderr}"
                }

            import json
            events_data = json.loads(result.stdout)

            # Normalize to list
            if isinstance(events_data, dict):
                events_data = [events_data]

            events = []
            for event in events_data:
                events.append({
                    "time_generated": event.get("TimeGenerated"),
                    "event_id": event.get("EventID"),
                    "event_type": event.get("EntryType"),
                    "source": event.get("Source"),
                    "description": event.get("Message"),
                    "computer": None
                })

            return {
                "status": "success",
                "log_name": log_name,
                "events": events,
                "count": len(events),
                "method": "powershell"
            }

        except Exception as e:
            logger.error(f"PowerShell event log error: {e}")
            return {"status": "error", "message": str(e)}

    def list_logs(self) -> Dict[str, Any]:
        """List available event logs"""
        if not IS_WINDOWS:
            return {
                "status": "error",
                "message": "Event log access not available (not Windows)"
            }

        try:
            command = 'Get-EventLog -List | Select-Object Log, MaximumKilobytes, OverflowAction, MinimumRetentionDays | ConvertTo-Json'

            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": f"PowerShell error: {result.stderr}"
                }

            import json
            logs_data = json.loads(result.stdout)

            # Normalize to list
            if isinstance(logs_data, dict):
                logs_data = [logs_data]

            return {
                "status": "success",
                "logs": logs_data,
                "count": len(logs_data)
            }

        except Exception as e:
            logger.error(f"List event logs error: {e}")
            return {"status": "error", "message": str(e)}

    def search_events(self, log_name: str, search_term: str,
                     max_events: int = 100) -> Dict[str, Any]:
        """
        Search for events containing specific text

        Args:
            log_name: Name of log
            search_term: Text to search for in event messages
            max_events: Maximum events to search

        Returns:
            Dict with matching events
        """
        result = self.read_events(log_name, max_events)

        if result["status"] != "success":
            return result

        # Filter events
        matching = [
            event for event in result["events"]
            if search_term.lower() in str(event.get("description", "")).lower()
        ]

        return {
            "status": "success",
            "log_name": log_name,
            "search_term": search_term,
            "events": matching,
            "count": len(matching)
        }

    def get_event_statistics(self, log_name: str, max_events: int = 1000) -> Dict[str, Any]:
        """
        Get statistics about events in a log

        Args:
            log_name: Name of log
            max_events: Number of recent events to analyze

        Returns:
            Dict with event statistics
        """
        result = self.read_events(log_name, max_events)

        if result["status"] != "success":
            return result

        # Calculate statistics
        type_counts = {}
        source_counts = {}
        event_id_counts = {}

        for event in result["events"]:
            event_type = event.get("event_type", "Unknown")
            source = event.get("source", "Unknown")
            event_id = event.get("event_id", 0)

            type_counts[event_type] = type_counts.get(event_type, 0) + 1
            source_counts[source] = source_counts.get(source, 0) + 1
            event_id_counts[event_id] = event_id_counts.get(event_id, 0) + 1

        # Sort by count
        top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_event_ids = sorted(event_id_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "status": "success",
            "log_name": log_name,
            "analyzed_events": len(result["events"]),
            "type_distribution": type_counts,
            "top_sources": [{"source": s, "count": c} for s, c in top_sources],
            "top_event_ids": [{"event_id": eid, "count": c} for eid, c in top_event_ids]
        }

    def clear_log(self, log_name: str, backup_path: str = None) -> Dict[str, Any]:
        """
        Clear an event log (requires admin privileges)

        Args:
            log_name: Name of log to clear
            backup_path: Optional path to backup log before clearing

        Returns:
            Dict with operation result
        """
        if not IS_WINDOWS:
            return {
                "status": "error",
                "message": "Event log access not available (not Windows)"
            }

        try:
            if backup_path:
                backup_cmd = f'wevtutil export-log "{log_name}" "{backup_path}"'
                subprocess.run(
                    ["cmd", "/c", backup_cmd],
                    check=True,
                    capture_output=True,
                    timeout=60
                )

            clear_cmd = f'wevtutil clear-log "{log_name}"'
            result = subprocess.run(
                ["cmd", "/c", clear_cmd],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": f"Log '{log_name}' cleared successfully",
                    "backup_path": backup_path
                }
            else:
                return {
                    "status": "error",
                    "message": f"Failed to clear log: {result.stderr}"
                }

        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Command failed: {e.stderr}"
            }
        except Exception as e:
            logger.error(f"Clear event log error: {e}")
            return {"status": "error", "message": str(e)}
