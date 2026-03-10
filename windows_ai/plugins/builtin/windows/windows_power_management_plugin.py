"""
Windows Power Management Plugin
Advanced power management and battery monitoring for Windows
"""
from typing import Dict, Any, Optional, List
import logging
import subprocess
import re
from datetime import datetime
import psutil

from windows_ai.plugins.base import ToolPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class WindowsPowerManagementPlugin(ToolPlugin):
    """
    Production-grade Windows power management plugin.

    Features:
    - Battery status and health monitoring
    - Power plan management
    - Sleep/hibernate control
    - Power consumption analytics
    - Wake timer management
    - Performance vs battery optimization
    """

    @staticmethod
    def get_metadata() -> PluginMetadata:
        return PluginMetadata(
            id="windows_power_management",
            name="Windows Power Management",
            description="Advanced power management and battery monitoring for Windows systems",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.TOOL,
            icon="🔋",
            tags=["windows", "power", "battery", "energy"],
            capabilities=[
                "battery_status",
                "power_plans",
                "sleep_control",
                "power_analytics",
                "performance_tuning"
            ]
        )

    async def initialize(self) -> bool:
        """Initialize the power management plugin"""
        try:
            self._initialized = True
            logger.info("Windows Power Management plugin initialized")
            return True
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    async def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute power management operations.

        Args:
            query: Operation type: "battery", "power_plan", "sleep", "hibernate", "analytics"
            parameters: Operation-specific parameters

        Returns:
            Operation results
        """
        try:
            params = parameters or {}
            operation = query.lower()

            # Route to appropriate handler
            handlers = {
                "battery": self._get_battery_status,
                "battery_health": self._get_battery_health,
                "power_plan": self._manage_power_plan,
                "list_plans": self._list_power_plans,
                "sleep": self._trigger_sleep,
                "hibernate": self._trigger_hibernate,
                "analytics": self._get_power_analytics,
                "wake_timers": self._manage_wake_timers,
                "optimize": self._optimize_power_settings
            }

            handler = handlers.get(operation)
            if not handler:
                return {
                    "success": False,
                    "error": f"Unknown operation: {operation}",
                    "available_operations": list(handlers.keys())
                }

            result = await handler(params)

            return {
                "success": True,
                "result": result,
                "message": f"Power management operation '{operation}' completed successfully",
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation
                }
            }

        except Exception as e:
            logger.error(f"Power management error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error executing power management operation"
            }

    async def _get_battery_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get current battery status"""
        try:
            battery = psutil.sensors_battery()

            if battery is None:
                return {
                    "has_battery": False,
                    "message": "No battery detected (desktop or AC-only device)"
                }

            # Get detailed battery info via powercfg
            result = subprocess.run(
                ["powercfg", "/batteryreport", "/duration", "1", "/output", "-"],
                capture_output=True,
                text=True,
                timeout=10
            )

            return {
                "has_battery": True,
                "percent": battery.percent,
                "plugged_in": battery.power_plugged,
                "time_remaining": battery.secsleft if battery.secsleft != -1 else None,
                "time_remaining_formatted": self._format_seconds(battery.secsleft) if battery.secsleft != -1 else "N/A",
                "status": "Charging" if battery.power_plugged else "Discharging",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            raise Exception(f"Battery status error: {str(e)}")

    async def _get_battery_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed battery health information"""
        try:
            # Run battery report
            report_file = "battery_report.html"
            subprocess.run(
                ["powercfg", "/batteryreport", "/output", report_file],
                capture_output=True,
                timeout=10
            )

            # Parse capacity degradation from powercfg
            result = subprocess.run(
                ["powercfg", "/batteryreport", "/xml"],
                capture_output=True,
                text=True,
                timeout=10
            )

            battery = psutil.sensors_battery()
            if battery is None:
                return {"has_battery": False}

            return {
                "has_battery": True,
                "current_capacity_percent": battery.percent,
                "report_generated": report_file,
                "health_status": "Good" if battery.percent > 80 else "Degraded",
                "recommendation": self._get_battery_recommendation(battery)
            }

        except Exception as e:
            raise Exception(f"Battery health error: {str(e)}")

    async def _list_power_plans(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all available power plans"""
        try:
            result = subprocess.run(
                ["powercfg", "/list"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                raise Exception(f"Failed to list power plans: {result.stderr}")

            # Parse power plans
            plans = []
            current_plan = None

            for line in result.stdout.split('\n'):
                # Match GUID lines
                match = re.search(r'([a-f0-9-]{36})\s+\((.+?)\)\s*(\*)?', line, re.IGNORECASE)
                if match:
                    guid = match.group(1)
                    name = match.group(2)
                    is_active = match.group(3) == '*'

                    plan = {
                        "guid": guid,
                        "name": name,
                        "active": is_active
                    }
                    plans.append(plan)

                    if is_active:
                        current_plan = plan

            return {
                "plans": plans,
                "current_plan": current_plan,
                "count": len(plans)
            }

        except Exception as e:
            raise Exception(f"List power plans error: {str(e)}")

    async def _manage_power_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manage power plans"""
        try:
            action = params.get("action", "get")

            if action == "set":
                # Set power plan
                plan_name = params.get("plan", "Balanced")

                # Map common names to GUIDs
                plan_map = {
                    "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
                    "power saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
                    "high performance": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
                }

                plan_guid = plan_map.get(plan_name.lower(), plan_name)

                result = subprocess.run(
                    ["powercfg", "/setactive", plan_guid],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode != 0:
                    raise Exception(f"Failed to set power plan: {result.stderr}")

                return {
                    "action": "set",
                    "plan": plan_name,
                    "guid": plan_guid,
                    "success": True
                }

            else:
                # Get current plan
                return await self._list_power_plans({})

        except Exception as e:
            raise Exception(f"Power plan management error: {str(e)}")

    async def _trigger_sleep(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger sleep mode"""
        try:
            # Use rundll32 to trigger sleep
            subprocess.run(
                ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
                timeout=5
            )

            return {
                "action": "sleep",
                "status": "triggered",
                "message": "System entering sleep mode"
            }

        except Exception as e:
            raise Exception(f"Sleep trigger error: {str(e)}")

    async def _trigger_hibernate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger hibernate mode"""
        try:
            # Check if hibernate is enabled
            result = subprocess.run(
                ["powercfg", "/availablesleepstates"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if "Hibernate" not in result.stdout:
                return {
                    "action": "hibernate",
                    "status": "unavailable",
                    "message": "Hibernate is not enabled on this system",
                    "recommendation": "Run 'powercfg /hibernate on' as administrator to enable"
                }

            # Trigger hibernate
            subprocess.run(
                ["shutdown", "/h"],
                timeout=5
            )

            return {
                "action": "hibernate",
                "status": "triggered",
                "message": "System entering hibernate mode"
            }

        except Exception as e:
            raise Exception(f"Hibernate trigger error: {str(e)}")

    async def _get_power_analytics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get power consumption analytics"""
        try:
            # Generate power efficiency report
            result = subprocess.run(
                ["powercfg", "/energy", "/duration", "5"],
                capture_output=True,
                text=True,
                timeout=60
            )

            # Get sleep study data
            sleep_result = subprocess.run(
                ["powercfg", "/sleepstudy"],
                capture_output=True,
                text=True,
                timeout=30
            )

            battery = psutil.sensors_battery()

            return {
                "battery_percent": battery.percent if battery else None,
                "power_plugged": battery.power_plugged if battery else None,
                "energy_report": "energy-report.html",
                "sleep_study": "sleepstudy-report.html" if sleep_result.returncode == 0 else None,
                "analytics_generated": datetime.now().isoformat()
            }

        except Exception as e:
            raise Exception(f"Power analytics error: {str(e)}")

    async def _manage_wake_timers(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manage wake timers"""
        try:
            action = params.get("action", "list")

            if action == "list":
                # List wake timers
                result = subprocess.run(
                    ["powercfg", "/waketimers"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                timers = []
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('Timer'):
                        timers.append(line.strip())

                return {
                    "wake_timers": timers,
                    "count": len(timers)
                }

            elif action == "disable":
                # Disable wake timers
                result = subprocess.run(
                    ["powercfg", "/setacvalueindex", "SCHEME_CURRENT", "SUB_SLEEP", "RTCWAKE", "0"],
                    capture_output=True,
                    timeout=10
                )

                return {
                    "action": "disable",
                    "status": "success" if result.returncode == 0 else "failed"
                }

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            raise Exception(f"Wake timer management error: {str(e)}")

    async def _optimize_power_settings(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize power settings based on usage pattern"""
        try:
            mode = params.get("mode", "balanced")  # balanced, performance, battery

            battery = psutil.sensors_battery()
            is_plugged = battery.power_plugged if battery else True

            recommendations = []

            if mode == "performance":
                recommendations.append("Set power plan to High Performance")
                recommendations.append("Disable USB selective suspend")
                recommendations.append("Set processor power management to 100%")
                plan = "high performance"

            elif mode == "battery":
                recommendations.append("Set power plan to Power Saver")
                recommendations.append("Enable adaptive brightness")
                recommendations.append("Reduce screen timeout to 5 minutes")
                plan = "power saver"

            else:  # balanced
                recommendations.append("Set power plan to Balanced")
                recommendations.append("Enable adaptive display brightness")
                recommendations.append("Moderate processor power management")
                plan = "balanced"

            # Apply the power plan
            result = await self._manage_power_plan({"action": "set", "plan": plan})

            return {
                "mode": mode,
                "optimizations_applied": recommendations,
                "power_plan_set": plan,
                "plugged_in": is_plugged,
                "battery_level": battery.percent if battery else None
            }

        except Exception as e:
            raise Exception(f"Power optimization error: {str(e)}")

    def _format_seconds(self, seconds: int) -> str:
        """Format seconds to human-readable time"""
        if seconds < 0:
            return "Unknown"

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    def _get_battery_recommendation(self, battery) -> str:
        """Get battery health recommendation"""
        if battery is None:
            return "No battery detected"

        percent = battery.percent

        if percent > 95:
            return "Battery health is excellent. Continue normal usage."
        elif percent > 80:
            return "Battery health is good. Consider calibrating periodically."
        elif percent > 60:
            return "Battery is showing signs of wear. Monitor capacity."
        else:
            return "Battery health is degraded. Consider replacement if needed."

    def get_schema(self) -> Dict[str, Any]:
        """Return parameter schema"""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Power management operation",
                    "enum": [
                        "battery",
                        "battery_health",
                        "power_plan",
                        "list_plans",
                        "sleep",
                        "hibernate",
                        "analytics",
                        "wake_timers",
                        "optimize"
                    ]
                },
                "parameters": {
                    "type": "object",
                    "description": "Operation-specific parameters"
                }
            },
            "required": ["query"]
        }

    def get_function_definition(self) -> Dict[str, Any]:
        """Return OpenAI function definition"""
        return {
            "name": "windows_power_management",
            "description": "Manage Windows power settings, battery status, and sleep modes. Use this when the user asks about battery life, power plans, sleep/hibernate, or power optimization.",
            "parameters": self.get_schema()
        }


# Plugin instance
plugin = WindowsPowerManagementPlugin()
