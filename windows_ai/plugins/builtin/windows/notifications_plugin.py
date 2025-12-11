"""
Windows Notifications Plugin for Windows AI
Comprehensive toast notification and action center management
"""

import asyncio
import subprocess
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from windows_ai.plugins.base import IntegrationPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class NotificationsPlugin(IntegrationPlugin):
    """
    Comprehensive Windows Notifications management plugin.
    
    Provides 35+ actions for:
    - Toast notification creation and management
    - Action Center control
    - Focus Assist settings
    - Notification history
    - App notification permissions
    - Badge and tile updates
    - Scheduled notifications
    - Interactive notifications with actions
    """

    def __init__(self):
        metadata = PluginMetadata(
            id="windows-notifications",
            name="Windows Notifications",
            description="Comprehensive Windows toast notification and action center management",
            version="2.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.INTEGRATION,
            tags=["windows", "notifications", "toast", "action-center", "focus-assist", "alerts"],
            requirements=["pywin32"]
        )
        super().__init__(metadata)
        
        self._actions = {
            # Toast Notifications
            "send_toast": self._send_toast,
            "send_simple_toast": self._send_simple_toast,
            "send_toast_with_actions": self._send_toast_with_actions,
            "send_toast_with_image": self._send_toast_with_image,
            "send_toast_with_progress": self._send_toast_with_progress,
            "update_toast_progress": self._update_toast_progress,
            "remove_toast": self._remove_toast,
            "clear_all_toasts": self._clear_all_toasts,
            
            # Action Center
            "get_action_center_status": self._get_action_center_status,
            "open_action_center": self._open_action_center,
            "close_action_center": self._close_action_center,
            "clear_action_center": self._clear_action_center,
            "get_notification_count": self._get_notification_count,
            
            # Focus Assist
            "get_focus_assist_status": self._get_focus_assist_status,
            "set_focus_assist": self._set_focus_assist,
            "enable_focus_assist": self._enable_focus_assist,
            "disable_focus_assist": self._disable_focus_assist,
            "get_focus_assist_settings": self._get_focus_assist_settings,
            "set_priority_list": self._set_priority_list,
            "get_priority_list": self._get_priority_list,
            
            # Notification History
            "get_notification_history": self._get_notification_history,
            "clear_notification_history": self._clear_notification_history,
            "get_notifications_by_app": self._get_notifications_by_app,
            
            # App Permissions
            "get_app_notification_settings": self._get_app_notification_settings,
            "set_app_notification_enabled": self._set_app_notification_enabled,
            "get_notification_permissions": self._get_notification_permissions,
            "reset_app_notification_settings": self._reset_app_notification_settings,
            
            # Badges and Tiles
            "set_badge_number": self._set_badge_number,
            "clear_badge": self._clear_badge,
            "update_tile": self._update_tile,
            "clear_tile": self._clear_tile,
            
            # Scheduled Notifications
            "schedule_notification": self._schedule_notification,
            "cancel_scheduled_notification": self._cancel_scheduled_notification,
            "get_scheduled_notifications": self._get_scheduled_notifications,
            
            # System Settings
            "get_notification_settings": self._get_notification_settings,
            "set_notification_sound": self._set_notification_sound,
            "set_notification_banner": self._set_notification_banner,
            "open_notification_settings": self._open_notification_settings
        }

    async def initialize(self) -> bool:
        """Initialize the Notifications plugin."""
        try:
            logger.info("Initializing Windows Notifications plugin")
            self._initialized = True
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Notifications plugin: {e}")
            return False

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute a notification action."""
        action = kwargs.get("action", "get_action_center_status")
        
        if action not in self._actions:
            return {
                "status": "error",
                "error": f"Unknown action: {action}",
                "available_actions": list(self._actions.keys())
            }
        
        try:
            result = await self._actions[action](**kwargs)
            return {
                "status": "success",
                "action": action,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Action {action} failed: {e}")
            return {
                "status": "error",
                "action": action,
                "error": str(e)
            }

    async def _run_powershell(self, script: str) -> Dict[str, Any]:
        """Execute a PowerShell script and return results."""
        try:
            process = await asyncio.create_subprocess_exec(
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command", script,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode("utf-8", errors="replace").strip(),
                "stderr": stderr.decode("utf-8", errors="replace").strip(),
                "return_code": process.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ==================== Toast Notifications ====================

    async def _send_toast(self, **kwargs) -> Dict[str, Any]:
        """Send a toast notification with full customization."""
        title = kwargs.get("title", "Windows AI")
        message = kwargs.get("message", "Notification")
        app_id = kwargs.get("app_id", "Windows AI")
        icon = kwargs.get("icon", "")
        sound = kwargs.get("sound", "Default")
        duration = kwargs.get("duration", "Short")  # Short or Long
        tag = kwargs.get("tag", "")
        group = kwargs.get("group", "")
        
        script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast duration="{duration}">
    <visual>
        <binding template="ToastGeneric">
            <text>{title}</text>
            <text>{message}</text>
            {"<image placement='appLogoOverride' src='" + icon + "'/>" if icon else ""}
        </binding>
    </visual>
    <audio src="ms-winsoundevent:Notification.{sound}"/>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)

$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
{f'$toast.Tag = "{tag}"' if tag else ''}
{f'$toast.Group = "{group}"' if group else ''}

$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("{app_id}")
$notifier.Show($toast)

@{{
    status = "sent"
    title = "{title}"
    tag = "{tag}"
    group = "{group}"
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "sent", "title": title}
        return {"error": result.get("stderr", result.get("error", "Unknown error"))}

    async def _send_simple_toast(self, **kwargs) -> Dict[str, Any]:
        """Send a simple toast notification."""
        title = kwargs.get("title", "Notification")
        message = kwargs.get("message", "")
        
        script = f'''
Add-Type -AssemblyName System.Windows.Forms
$balloon = New-Object System.Windows.Forms.NotifyIcon
$balloon.Icon = [System.Drawing.SystemIcons]::Information
$balloon.BalloonTipTitle = "{title}"
$balloon.BalloonTipText = "{message}"
$balloon.Visible = $true
$balloon.ShowBalloonTip(5000)
Start-Sleep -Milliseconds 100
@{{ status = "sent"; title = "{title}" }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "sent"}
        return {"error": result.get("stderr", "Failed to send notification")}

    async def _send_toast_with_actions(self, **kwargs) -> Dict[str, Any]:
        """Send toast with action buttons."""
        title = kwargs.get("title", "Windows AI")
        message = kwargs.get("message", "")
        actions = kwargs.get("actions", [])  # List of {"content": "...", "arguments": "..."}
        
        action_xml = ""
        for action in actions[:5]:  # Max 5 actions
            content = action.get("content", "Action")
            arguments = action.get("arguments", "")
            action_xml += f'<action content="{content}" arguments="{arguments}"/>'
        
        script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{title}</text>
            <text>{message}</text>
        </binding>
    </visual>
    <actions>
        {action_xml}
    </actions>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Windows AI")
$notifier.Show($toast)
@{{ status = "sent"; actions = {len(actions)} }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "sent", "actions": len(actions)}
        return {"error": result.get("stderr", "Failed to send notification")}

    async def _send_toast_with_image(self, **kwargs) -> Dict[str, Any]:
        """Send toast with hero or inline image."""
        title = kwargs.get("title", "Windows AI")
        message = kwargs.get("message", "")
        image_path = kwargs.get("image_path", "")
        image_placement = kwargs.get("placement", "hero")  # hero or inline
        
        placement_attr = 'placement="hero"' if image_placement == "hero" else ""
        
        script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{title}</text>
            <text>{message}</text>
            <image src="{image_path}" {placement_attr}/>
        </binding>
    </visual>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Windows AI")
$notifier.Show($toast)
@{{ status = "sent"; image = "{image_path}" }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "sent"}
        return {"error": result.get("stderr", "Failed to send notification")}

    async def _send_toast_with_progress(self, **kwargs) -> Dict[str, Any]:
        """Send toast with progress bar."""
        title = kwargs.get("title", "Download Progress")
        status_text = kwargs.get("status", "Downloading...")
        progress = kwargs.get("progress", 0.0)
        tag = kwargs.get("tag", "progress_toast")
        
        script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{title}</text>
            <progress value="{{{{progressValue}}}}" title="{{{{progressTitle}}}}" status="{{{{progressStatus}}}}"/>
        </binding>
    </visual>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)

$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
$toast.Tag = "{tag}"

$data = [Windows.UI.Notifications.NotificationData]::new()
$data.Values["progressValue"] = "{progress}"
$data.Values["progressTitle"] = "{title}"
$data.Values["progressStatus"] = "{status_text}"
$toast.Data = $data

$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Windows AI")
$notifier.Show($toast)
@{{ status = "sent"; tag = "{tag}"; progress = {progress} }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "sent", "tag": tag}
        return {"error": result.get("stderr", "Failed to send notification")}

    async def _update_toast_progress(self, **kwargs) -> Dict[str, Any]:
        """Update progress on existing toast."""
        tag = kwargs.get("tag", "progress_toast")
        progress = kwargs.get("progress", 0.0)
        status_text = kwargs.get("status", "Updating...")
        
        script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null

$data = [Windows.UI.Notifications.NotificationData]::new()
$data.Values["progressValue"] = "{progress}"
$data.Values["progressStatus"] = "{status_text}"
$data.SequenceNumber = [uint32]((Get-Date).Ticks % [uint32]::MaxValue)

$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Windows AI")
$result = $notifier.Update($data, "{tag}")

@{{
    status = "updated"
    tag = "{tag}"
    progress = {progress}
    update_result = $result.ToString()
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "updated", "tag": tag}
        return {"error": result.get("stderr", "Failed to update notification")}

    async def _remove_toast(self, **kwargs) -> Dict[str, Any]:
        """Remove a specific toast by tag."""
        tag = kwargs.get("tag", "")
        group = kwargs.get("group", "")
        
        script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null

$history = [Windows.UI.Notifications.ToastNotificationManager]::History
{"$history.Remove('" + tag + "', '" + group + "', 'Windows AI')" if group else "$history.Remove('" + tag + "', 'Windows AI')"}

@{{ status = "removed"; tag = "{tag}" }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "removed"}
        return {"error": result.get("stderr", "Failed to remove notification")}

    async def _clear_all_toasts(self, **kwargs) -> Dict[str, Any]:
        """Clear all toast notifications."""
        app_id = kwargs.get("app_id", "Windows AI")
        
        script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$history = [Windows.UI.Notifications.ToastNotificationManager]::History
$history.Clear("{app_id}")
@{{ status = "cleared"; app_id = "{app_id}" }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "cleared"}
        return {"error": result.get("stderr", "Failed to clear notifications")}

    # ==================== Action Center ====================

    async def _get_action_center_status(self, **kwargs) -> Dict[str, Any]:
        """Get Action Center status and settings."""
        script = '''
$settings = @{
    action_center_enabled = (Get-ItemProperty -Path "HKCU:\\Software\\Policies\\Microsoft\\Windows\\Explorer" -Name "DisableNotificationCenter" -ErrorAction SilentlyContinue).DisableNotificationCenter -ne 1
    quiet_hours_enabled = $false
}

try {
    $quietHours = Get-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings" -ErrorAction SilentlyContinue
    if ($quietHours) {
        $settings.quiet_hours_enabled = $quietHours.NOC_GLOBAL_SETTING_TOASTS_ENABLED -eq 0
    }
} catch {}

$settings | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"action_center_enabled": True}
        return {"error": result.get("stderr", "Failed to get status")}

    async def _open_action_center(self, **kwargs) -> Dict[str, Any]:
        """Open the Action Center."""
        script = '''
$shell = New-Object -ComObject Shell.Application
$shell.Open("ms-actioncenter:")
@{ status = "opened" } | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "opened"}

    async def _close_action_center(self, **kwargs) -> Dict[str, Any]:
        """Close the Action Center."""
        script = '''
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class ActionCenter {
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@
$hwnd = [ActionCenter]::FindWindow("Windows.UI.Core.CoreWindow", "Action center")
if ($hwnd -ne [IntPtr]::Zero) {
    [ActionCenter]::ShowWindow($hwnd, 0) | Out-Null
}
@{ status = "closed" } | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "closed"}

    async def _clear_action_center(self, **kwargs) -> Dict[str, Any]:
        """Clear all notifications from Action Center."""
        script = '''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$history = [Windows.UI.Notifications.ToastNotificationManager]::History
$history.Clear()
@{ status = "cleared" } | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "cleared"}

    async def _get_notification_count(self, **kwargs) -> Dict[str, Any]:
        """Get count of notifications in Action Center."""
        script = '''
try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    # Note: Direct count not available via API, estimate from registry
    $count = 0
    $notifPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Data"
    if (Test-Path $notifPath) {
        $count = (Get-ChildItem $notifPath -ErrorAction SilentlyContinue).Count
    }
    @{ count = $count; estimated = $true } | ConvertTo-Json
} catch {
    @{ count = 0; error = $_.Exception.Message } | ConvertTo-Json
}
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"count": 0}
        return {"count": 0}

    # ==================== Focus Assist ====================

    async def _get_focus_assist_status(self, **kwargs) -> Dict[str, Any]:
        """Get current Focus Assist status."""
        script = '''
$status = @{
    enabled = $false
    mode = "off"
}

try {
    $focusAssist = Get-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\DefaultAccount\\Current\\default`$windows.data.notifications.quiethourssettings\\windows.data.notifications.quiethourssettings" -ErrorAction SilentlyContinue
    
    $regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"
    $settings = Get-ItemProperty -Path $regPath -ErrorAction SilentlyContinue
    
    if ($settings.NOC_GLOBAL_SETTING_TOASTS_ENABLED -eq 0) {
        $status.enabled = $true
        $status.mode = "alarms_only"
    }
} catch {}

$status | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"enabled": False, "mode": "off"}
        return {"enabled": False, "mode": "off"}

    async def _set_focus_assist(self, **kwargs) -> Dict[str, Any]:
        """Set Focus Assist mode."""
        mode = kwargs.get("mode", "off")  # off, priority_only, alarms_only
        
        script = f'''
# Focus Assist is controlled through complex cloud store registry
# This is a simplified version using notification settings
$regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"

switch ("{mode}") {{
    "off" {{
        Set-ItemProperty -Path $regPath -Name "NOC_GLOBAL_SETTING_TOASTS_ENABLED" -Value 1 -Type DWord -Force
    }}
    "priority_only" {{
        Set-ItemProperty -Path $regPath -Name "NOC_GLOBAL_SETTING_TOASTS_ENABLED" -Value 0 -Type DWord -Force
    }}
    "alarms_only" {{
        Set-ItemProperty -Path $regPath -Name "NOC_GLOBAL_SETTING_TOASTS_ENABLED" -Value 0 -Type DWord -Force
    }}
}}

@{{ status = "set"; mode = "{mode}" }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "set", "mode": mode}
        return {"error": result.get("stderr", "Failed to set mode")}

    async def _enable_focus_assist(self, **kwargs) -> Dict[str, Any]:
        """Enable Focus Assist (alarms only mode)."""
        return await self._set_focus_assist(mode="alarms_only")

    async def _disable_focus_assist(self, **kwargs) -> Dict[str, Any]:
        """Disable Focus Assist."""
        return await self._set_focus_assist(mode="off")

    async def _get_focus_assist_settings(self, **kwargs) -> Dict[str, Any]:
        """Get Focus Assist configuration settings."""
        script = '''
$settings = @{
    automatic_rules = @{
        during_hours = $false
        during_hours_start = ""
        during_hours_end = ""
        when_duplicating = $false
        when_gaming = $false
    }
    priority_list = @()
}

try {
    $rulesPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\CloudStore\\Store\\DefaultAccount\\Current"
    $settings.automatic_rules.when_gaming = (Get-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR" -Name "AppCaptureEnabled" -ErrorAction SilentlyContinue).AppCaptureEnabled -eq 1
} catch {}

$settings | ConvertTo-Json -Depth 5
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"automatic_rules": {}}
        return {"error": result.get("stderr", "Failed to get settings")}

    async def _set_priority_list(self, **kwargs) -> Dict[str, Any]:
        """Set apps in Focus Assist priority list."""
        apps = kwargs.get("apps", [])
        return {"status": "not_implemented", "note": "Priority list requires Windows Settings UI"}

    async def _get_priority_list(self, **kwargs) -> Dict[str, Any]:
        """Get Focus Assist priority list."""
        return {"priority_apps": [], "note": "Priority list stored in cloud store"}

    # ==================== Notification History ====================

    async def _get_notification_history(self, **kwargs) -> Dict[str, Any]:
        """Get notification history."""
        limit = kwargs.get("limit", 50)
        
        script = f'''
$notifications = @()
$dbPath = "$env:LOCALAPPDATA\\Microsoft\\Windows\\Notifications\\wpndatabase.db"

if (Test-Path $dbPath) {{
    # Database is locked by system, read from registry instead
    $notifPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\PushNotifications"
    if (Test-Path $notifPath) {{
        $apps = Get-ChildItem $notifPath -ErrorAction SilentlyContinue
        foreach ($app in $apps | Select-Object -First {limit}) {{
            $notifications += @{{
                app = $app.PSChildName
                path = $app.PSPath
            }}
        }}
    }}
}}

@{{
    notifications = $notifications
    count = $notifications.Count
    limit = {limit}
}} | ConvertTo-Json -Depth 3
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"notifications": [], "count": 0}
        return {"notifications": [], "count": 0}

    async def _clear_notification_history(self, **kwargs) -> Dict[str, Any]:
        """Clear notification history."""
        script = '''
# Clear notification database requires elevated permissions
# Clear user-accessible notification data
$cleared = 0
try {
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    $history = [Windows.UI.Notifications.ToastNotificationManager]::History
    $history.Clear()
    $cleared = 1
} catch {}

@{ status = "cleared"; cleared_count = $cleared } | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "cleared"}

    async def _get_notifications_by_app(self, **kwargs) -> Dict[str, Any]:
        """Get notifications grouped by app."""
        app_id = kwargs.get("app_id", "")
        
        script = f'''
$appNotifications = @()
$notifPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"

if (Test-Path $notifPath) {{
    $apps = Get-ChildItem $notifPath -ErrorAction SilentlyContinue
    foreach ($app in $apps) {{
        $appName = $app.PSChildName
        {"if ($appName -like '*" + app_id + "*') {" if app_id else ""}
        $settings = Get-ItemProperty $app.PSPath -ErrorAction SilentlyContinue
        $appNotifications += @{{
            app_id = $appName
            enabled = $settings.Enabled -ne 0
            show_in_action_center = $settings.ShowInActionCenter -ne 0
        }}
        {"}" if app_id else ""}
    }}
}}

@{{
    apps = $appNotifications
    count = $appNotifications.Count
}} | ConvertTo-Json -Depth 3
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"apps": [], "count": 0}
        return {"apps": [], "count": 0}

    # ==================== App Permissions ====================

    async def _get_app_notification_settings(self, **kwargs) -> Dict[str, Any]:
        """Get notification settings for a specific app."""
        app_id = kwargs.get("app_id", "")
        
        if not app_id:
            return {"error": "app_id is required"}
        
        script = f'''
$settings = @{{
    app_id = "{app_id}"
    enabled = $true
    show_banner = $true
    show_in_action_center = $true
    play_sound = $true
    priority = "default"
}}

$regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings\\{app_id}"
if (Test-Path $regPath) {{
    $props = Get-ItemProperty $regPath -ErrorAction SilentlyContinue
    $settings.enabled = $props.Enabled -ne 0
    $settings.show_banner = $props.ShowBanner -ne 0  
    $settings.show_in_action_center = $props.ShowInActionCenter -ne 0
    $settings.play_sound = $props.AllowSound -ne 0
}}

$settings | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"app_id": app_id, "enabled": True}
        return {"app_id": app_id, "enabled": True}

    async def _set_app_notification_enabled(self, **kwargs) -> Dict[str, Any]:
        """Enable or disable notifications for an app."""
        app_id = kwargs.get("app_id", "")
        enabled = kwargs.get("enabled", True)
        
        if not app_id:
            return {"error": "app_id is required"}
        
        value = 1 if enabled else 0
        script = f'''
$regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings\\{app_id}"
if (-not (Test-Path $regPath)) {{
    New-Item -Path $regPath -Force | Out-Null
}}
Set-ItemProperty -Path $regPath -Name "Enabled" -Value {value} -Type DWord -Force
@{{ app_id = "{app_id}"; enabled = ${str(enabled).lower()} }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            return {"app_id": app_id, "enabled": enabled}
        return {"error": result.get("stderr", "Failed to set app notification")}

    async def _get_notification_permissions(self, **kwargs) -> Dict[str, Any]:
        """Get notification permissions for all apps."""
        script = '''
$permissions = @()
$notifPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"

if (Test-Path $notifPath) {
    $apps = Get-ChildItem $notifPath -ErrorAction SilentlyContinue
    foreach ($app in $apps | Select-Object -First 100) {
        $props = Get-ItemProperty $app.PSPath -ErrorAction SilentlyContinue
        $permissions += @{
            app_id = $app.PSChildName
            enabled = $props.Enabled -ne 0
            show_banner = $props.ShowBanner -ne 0
        }
    }
}

@{
    permissions = $permissions
    count = $permissions.Count
} | ConvertTo-Json -Depth 3
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"permissions": [], "count": 0}
        return {"permissions": [], "count": 0}

    async def _reset_app_notification_settings(self, **kwargs) -> Dict[str, Any]:
        """Reset notification settings for an app to defaults."""
        app_id = kwargs.get("app_id", "")
        
        if not app_id:
            return {"error": "app_id is required"}
        
        script = f'''
$regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings\\{app_id}"
if (Test-Path $regPath) {{
    Remove-Item -Path $regPath -Recurse -Force
    @{{ app_id = "{app_id}"; status = "reset" }} | ConvertTo-Json
}} else {{
    @{{ app_id = "{app_id}"; status = "not_found" }} | ConvertTo-Json
}}
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"app_id": app_id, "status": "reset"}
        return {"error": result.get("stderr", "Failed to reset settings")}

    # ==================== Badges and Tiles ====================

    async def _set_badge_number(self, **kwargs) -> Dict[str, Any]:
        """Set badge number on app tile."""
        number = kwargs.get("number", 0)
        app_id = kwargs.get("app_id", "Windows AI")
        
        script = f'''
[Windows.UI.Notifications.BadgeUpdateManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = '<badge value="{number}"/>'
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)

$badge = [Windows.UI.Notifications.BadgeNotification]::new($xml)
$updater = [Windows.UI.Notifications.BadgeUpdateManager]::CreateBadgeUpdaterForApplication()
$updater.Update($badge)

@{{ status = "set"; number = {number} }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "set", "number": number}

    async def _clear_badge(self, **kwargs) -> Dict[str, Any]:
        """Clear badge from app tile."""
        script = '''
[Windows.UI.Notifications.BadgeUpdateManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$updater = [Windows.UI.Notifications.BadgeUpdateManager]::CreateBadgeUpdaterForApplication()
$updater.Clear()
@{ status = "cleared" } | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "cleared"}

    async def _update_tile(self, **kwargs) -> Dict[str, Any]:
        """Update live tile content."""
        title = kwargs.get("title", "")
        message = kwargs.get("message", "")
        
        script = f'''
[Windows.UI.Notifications.TileUpdateManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<tile>
    <visual>
        <binding template="TileMedium">
            <text hint-style="caption">{title}</text>
            <text hint-style="captionSubtle">{message}</text>
        </binding>
    </visual>
</tile>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)

$tile = [Windows.UI.Notifications.TileNotification]::new($xml)
$updater = [Windows.UI.Notifications.TileUpdateManager]::CreateTileUpdaterForApplication()
$updater.Update($tile)

@{{ status = "updated"; title = "{title}" }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "updated", "title": title}

    async def _clear_tile(self, **kwargs) -> Dict[str, Any]:
        """Clear live tile content."""
        script = '''
[Windows.UI.Notifications.TileUpdateManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
$updater = [Windows.UI.Notifications.TileUpdateManager]::CreateTileUpdaterForApplication()
$updater.Clear()
@{ status = "cleared" } | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "cleared"}

    # ==================== Scheduled Notifications ====================

    async def _schedule_notification(self, **kwargs) -> Dict[str, Any]:
        """Schedule a notification for future delivery."""
        title = kwargs.get("title", "Scheduled Notification")
        message = kwargs.get("message", "")
        deliver_at = kwargs.get("deliver_at", "")  # ISO format datetime
        tag = kwargs.get("tag", f"scheduled_{datetime.now().timestamp()}")
        
        if not deliver_at:
            return {"error": "deliver_at datetime is required (ISO format)"}
        
        script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{title}</text>
            <text>{message}</text>
        </binding>
    </visual>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)

$deliveryTime = [DateTime]::Parse("{deliver_at}")
$scheduledToast = [Windows.UI.Notifications.ScheduledToastNotification]::new($xml, $deliveryTime)
$scheduledToast.Tag = "{tag}"

$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Windows AI")
$notifier.AddToSchedule($scheduledToast)

@{{
    status = "scheduled"
    tag = "{tag}"
    deliver_at = "{deliver_at}"
}} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "scheduled", "tag": tag}
        return {"error": result.get("stderr", "Failed to schedule notification")}

    async def _cancel_scheduled_notification(self, **kwargs) -> Dict[str, Any]:
        """Cancel a scheduled notification."""
        tag = kwargs.get("tag", "")
        
        if not tag:
            return {"error": "tag is required"}
        
        script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null

$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Windows AI")
$scheduled = $notifier.GetScheduledToastNotifications()

$found = $false
foreach ($toast in $scheduled) {{
    if ($toast.Tag -eq "{tag}") {{
        $notifier.RemoveFromSchedule($toast)
        $found = $true
        break
    }}
}}

@{{ status = if ($found) {{ "cancelled" }} else {{ "not_found" }}; tag = "{tag}" }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"status": "cancelled", "tag": tag}
        return {"error": result.get("stderr", "Failed to cancel notification")}

    async def _get_scheduled_notifications(self, **kwargs) -> Dict[str, Any]:
        """Get all scheduled notifications."""
        script = '''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null

$notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Windows AI")
$scheduled = $notifier.GetScheduledToastNotifications()

$notifications = @()
foreach ($toast in $scheduled) {
    $notifications += @{
        tag = $toast.Tag
        group = $toast.Group
        delivery_time = $toast.DeliveryTime.ToString("o")
    }
}

@{
    scheduled = $notifications
    count = $notifications.Count
} | ConvertTo-Json -Depth 3
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"scheduled": [], "count": 0}
        return {"scheduled": [], "count": 0}

    # ==================== System Settings ====================

    async def _get_notification_settings(self, **kwargs) -> Dict[str, Any]:
        """Get global notification settings."""
        script = '''
$settings = @{
    notifications_enabled = $true
    lock_screen_notifications = $true
    show_reminders = $true
    show_voip_calls = $true
    play_sounds = $true
}

$regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"
if (Test-Path $regPath) {
    $props = Get-ItemProperty $regPath -ErrorAction SilentlyContinue
    $settings.notifications_enabled = $props.NOC_GLOBAL_SETTING_TOASTS_ENABLED -ne 0
}

$lockPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Lock Screen"
if (Test-Path $lockPath) {
    $lockProps = Get-ItemProperty $lockPath -ErrorAction SilentlyContinue
    $settings.lock_screen_notifications = $lockProps.LockScreenNotifications -ne 0
}

$settings | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        if result["success"]:
            try:
                return json.loads(result["stdout"])
            except:
                return {"notifications_enabled": True}
        return {"notifications_enabled": True}

    async def _set_notification_sound(self, **kwargs) -> Dict[str, Any]:
        """Enable or disable notification sounds."""
        enabled = kwargs.get("enabled", True)
        
        value = 1 if enabled else 0
        script = f'''
$regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"
Set-ItemProperty -Path $regPath -Name "NOC_GLOBAL_SETTING_ALLOW_NOTIFICATION_SOUND" -Value {value} -Type DWord -Force
@{{ sound_enabled = ${str(enabled).lower()} }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"sound_enabled": enabled}

    async def _set_notification_banner(self, **kwargs) -> Dict[str, Any]:
        """Enable or disable notification banners."""
        enabled = kwargs.get("enabled", True)
        
        value = 1 if enabled else 0
        script = f'''
$regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"
Set-ItemProperty -Path $regPath -Name "NOC_GLOBAL_SETTING_ALLOW_TOASTS_ABOVE_LOCK" -Value {value} -Type DWord -Force
@{{ banners_enabled = ${str(enabled).lower()} }} | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"banners_enabled": enabled}

    async def _open_notification_settings(self, **kwargs) -> Dict[str, Any]:
        """Open Windows notification settings."""
        script = '''
Start-Process "ms-settings:notifications"
@{ status = "opened" } | ConvertTo-Json
'''
        result = await self._run_powershell(script)
        return {"status": "opened"}

    async def cleanup(self):
        """Cleanup plugin resources."""
        self._initialized = False
        logger.info("Windows Notifications plugin cleaned up")
