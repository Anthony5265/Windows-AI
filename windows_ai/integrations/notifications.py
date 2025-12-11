"""
Notifications Manager - 15+ Services
Push, SMS, WebSocket, Desktop notifications
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from windows_ai.config.unified_config import WindowsAIConfig

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class NotificationsManager:
    """Unified notifications across 15+ channels"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True

    # ==================== PUSH NOTIFICATIONS ====================

    async def cleanup(self):
        """Cleanup resources before shutdown"""
        try:
            # Close any open connections
            if hasattr(self, '_clients'):
                for client in self._clients.values():
                    if hasattr(client, 'close'):
                        await client.close() if asyncio.iscoroutinefunction(client.close) else client.close()
            
            # Reset initialization flag
            self._initialized = False
            logger.info(f"{self.__class__.__name__} cleanup completed")
            
        except Exception as e:
            logger.error(f"{self.__class__.__name__} cleanup failed: {e}")

    async def send_push(self, provider: str, tokens: List[str], title: str, body: str, data: Dict = None) -> Dict:
        """Send push notification"""
        if provider == "firebase":
            return await self._firebase_push(tokens, title, body, data)
        elif provider == "onesignal":
            return await self._onesignal_push(tokens, title, body, data)
        elif provider == "pusher":
            return await self._pusher_push(tokens, title, body, data)
        elif provider == "expo":
            return await self._expo_push(tokens, title, body, data)
        else:
            raise ValueError(f"Unsupported push provider: {provider}")

    async def _firebase_push(self, tokens, title, body, data):
        """Firebase Cloud Messaging"""
        import firebase_admin
        from firebase_admin import messaging

        if not firebase_admin._apps:
            firebase_admin.initialize_app()

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},
            tokens=tokens
        )
        response = messaging.send_multicast(message)
        return {"success_count": response.success_count, "failure_count": response.failure_count}

    async def _onesignal_push(self, tokens, title, body, data):
        """OneSignal push"""
        import aiohttp

        app_id = os.environ.get("ONESIGNAL_APP_ID")
        api_key = os.environ.get("ONESIGNAL_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://onesignal.com/api/v1/notifications",
                headers={"Authorization": f"Basic {api_key}", "Content-Type": "application/json"},
                json={
                    "app_id": app_id,
                    "include_player_ids": tokens,
                    "headings": {"en": title},
                    "contents": {"en": body},
                    "data": data or {}
                }
            ) as response:
                return await response.json()

    async def _pusher_push(self, tokens, title, body, data):
        """Pusher Beams"""
        from pusher_push_notifications import PushNotifications

        beams = PushNotifications(
            instance_id=os.environ.get("PUSHER_INSTANCE_ID"),
            secret_key=os.environ.get("PUSHER_SECRET_KEY")
        )

        response = beams.publish_to_users(
            user_ids=tokens,
            publish_body={"fcm": {"notification": {"title": title, "body": body}, "data": data or {}}}
        )
        return response

    async def _expo_push(self, tokens, title, body, data):
        """Expo Push Notifications"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://exp.host/--/api/v2/push/send",
                json=[{"to": token, "title": title, "body": body, "data": data or {}} for token in tokens]
            ) as response:
                return await response.json()

    # ==================== SMS ====================

    async def send_sms(self, provider: str, to: str, message: str, **kwargs) -> Dict:
        """Send SMS"""
        if provider == "twilio":
            return await self._twilio_sms(to, message, **kwargs)
        elif provider == "vonage":
            return await self._vonage_sms(to, message, **kwargs)
        elif provider == "messagebird":
            return await self._messagebird_sms(to, message, **kwargs)
        elif provider == "plivo":
            return await self._plivo_sms(to, message, **kwargs)
        else:
            raise ValueError(f"Unsupported SMS provider: {provider}")

    async def _twilio_sms(self, to, message, **kwargs):
        """Twilio SMS"""
        from twilio.rest import Client

        client = Client(os.environ.get("TWILIO_SID"), os.environ.get("TWILIO_AUTH_TOKEN"))
        msg = client.messages.create(
            body=message,
            from_=kwargs.get("from_number", os.environ.get("TWILIO_FROM")),
            to=to
        )
        return {"sid": msg.sid, "status": msg.status}

    async def _vonage_sms(self, to, message, **kwargs):
        """Vonage (Nexmo) SMS"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://rest.nexmo.com/sms/json",
                json={
                    "api_key": os.environ.get("VONAGE_API_KEY"),
                    "api_secret": os.environ.get("VONAGE_API_SECRET"),
                    "from": kwargs.get("from_number", "WindowsAI"),
                    "to": to,
                    "text": message
                }
            ) as response:
                return await response.json()

    async def _messagebird_sms(self, to, message, **kwargs):
        """MessageBird SMS"""
        import messagebird

        client = messagebird.Client(os.environ.get("MESSAGEBIRD_API_KEY"))
        msg = client.message_create(
            kwargs.get("from_number", "WindowsAI"),
            to,
            message
        )
        return {"id": msg.id}

    async def _plivo_sms(self, to, message, **kwargs):
        """Plivo SMS"""
        import plivo

        client = plivo.RestClient(os.environ.get("PLIVO_AUTH_ID"), os.environ.get("PLIVO_AUTH_TOKEN"))
        response = client.messages.create(
            src=kwargs.get("from_number", os.environ.get("PLIVO_FROM")),
            dst=to,
            text=message
        )
        return {"message_uuid": response["message_uuid"]}

    # ==================== DESKTOP ====================

    async def desktop_notification(self, title: str, body: str, icon: str = None) -> bool:
        """Windows desktop notification"""
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, body, icon_path=icon, duration=5, threaded=True)
            return True
        except ImportError:
            from plyer import notification
            notification.notify(title=title, message=body, app_icon=icon, timeout=5)
            return True

    # ==================== WEBSOCKET ====================

    async def broadcast_websocket(self, channel: str, event: str, data: Dict) -> bool:
        """Broadcast via Pusher Channels"""
        import pusher

        client = pusher.Pusher(
            app_id=os.environ.get("PUSHER_APP_ID"),
            key=os.environ.get("PUSHER_KEY"),
            secret=os.environ.get("PUSHER_SECRET"),
            cluster=os.environ.get("PUSHER_CLUSTER", "us2")
        )
        client.trigger(channel, event, data)
        return True

    # ==================== WEBHOOKS ====================

    async def send_webhook(self, url: str, payload: Dict, headers: Dict = None) -> Dict:
        """Send webhook notification"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers or {}) as response:
                return {"status": response.status, "body": await response.text()}

    def list_providers(self) -> Dict[str, List[str]]:
        return {
            "push": ["firebase", "onesignal", "pusher", "expo", "apns"],
            "sms": ["twilio", "vonage", "messagebird", "plivo", "sinch"],
            "other": ["desktop", "websocket", "webhook", "slack", "discord"]
        }
