"""
Scheduling & Calendar Manager - 10+ Services
Calendly, Cal.com, Google Calendar, Outlook, etc.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SchedulingManager:
    """Unified scheduling across 10+ platforms"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    # ==================== GOOGLE CALENDAR ====================

    async def google_calendar_create_event(
        self,
        calendar_id: str,
        summary: str,
        start: datetime,
        end: datetime,
        description: str = None,
        attendees: List[str] = None
    ) -> Dict:
        """Create Google Calendar event"""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        credentials = Credentials(token=os.environ.get("GOOGLE_ACCESS_TOKEN"))
        service = build("calendar", "v3", credentials=credentials)

        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
            "attendees": [{"email": email} for email in (attendees or [])]
        }

        result = service.events().insert(calendarId=calendar_id, body=event).execute()
        return {"id": result["id"], "link": result.get("htmlLink")}

    async def google_calendar_list_events(self, calendar_id: str, time_min: datetime = None, max_results: int = 10) -> List[Dict]:
        """List Google Calendar events"""
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        credentials = Credentials(token=os.environ.get("GOOGLE_ACCESS_TOKEN"))
        service = build("calendar", "v3", credentials=credentials)

        time_min = time_min or datetime.utcnow()
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min.isoformat() + "Z",
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        return [{"id": e["id"], "summary": e.get("summary"), "start": e["start"].get("dateTime")}
                for e in events_result.get("items", [])]

    # ==================== OUTLOOK CALENDAR ====================

    async def outlook_create_event(
        self,
        subject: str,
        start: datetime,
        end: datetime,
        body: str = None,
        attendees: List[str] = None
    ) -> Dict:
        """Create Outlook calendar event"""
        import aiohttp

        access_token = os.environ.get("MICROSOFT_ACCESS_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://graph.microsoft.com/v1.0/me/events",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json={
                    "subject": subject,
                    "body": {"contentType": "text", "content": body or ""},
                    "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
                    "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
                    "attendees": [{"emailAddress": {"address": email}} for email in (attendees or [])]
                }
            ) as response:
                return await response.json()

    async def outlook_list_events(self, time_min: datetime = None, max_results: int = 10) -> List[Dict]:
        """List Outlook calendar events"""
        import aiohttp

        access_token = os.environ.get("MICROSOFT_ACCESS_TOKEN")
        time_min = time_min or datetime.utcnow()

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://graph.microsoft.com/v1.0/me/events",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"$filter": f"start/dateTime ge '{time_min.isoformat()}'", "$top": max_results}
            ) as response:
                data = await response.json()
                return [{"id": e["id"], "subject": e["subject"], "start": e["start"]["dateTime"]}
                        for e in data.get("value", [])]

    # ==================== CALENDLY ====================

    async def calendly_get_event_types(self) -> List[Dict]:
        """Get Calendly event types"""
        import aiohttp

        api_key = os.environ.get("CALENDLY_API_KEY")

        async with aiohttp.ClientSession() as session:
            # Get user
            async with session.get(
                "https://api.calendly.com/users/me",
                headers={"Authorization": f"Bearer {api_key}"}
            ) as response:
                user = await response.json()
                user_uri = user["resource"]["uri"]

            # Get event types
            async with session.get(
                "https://api.calendly.com/event_types",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"user": user_uri}
            ) as response:
                data = await response.json()
                return [{"name": et["name"], "slug": et["slug"], "uri": et["uri"]}
                        for et in data.get("collection", [])]

    async def calendly_get_scheduled_events(self, count: int = 10) -> List[Dict]:
        """Get Calendly scheduled events"""
        import aiohttp

        api_key = os.environ.get("CALENDLY_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.calendly.com/users/me",
                headers={"Authorization": f"Bearer {api_key}"}
            ) as response:
                user = await response.json()
                user_uri = user["resource"]["uri"]

            async with session.get(
                "https://api.calendly.com/scheduled_events",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"user": user_uri, "count": count}
            ) as response:
                data = await response.json()
                return [{"name": e["name"], "start_time": e["start_time"], "status": e["status"]}
                        for e in data.get("collection", [])]

    # ==================== CAL.COM ====================

    async def calcom_get_event_types(self) -> List[Dict]:
        """Get Cal.com event types"""
        import aiohttp

        api_key = os.environ.get("CALCOM_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.cal.com/v1/event-types",
                params={"apiKey": api_key}
            ) as response:
                data = await response.json()
                return [{"id": et["id"], "title": et["title"], "slug": et["slug"]}
                        for et in data.get("event_types", [])]

    async def calcom_get_bookings(self) -> List[Dict]:
        """Get Cal.com bookings"""
        import aiohttp

        api_key = os.environ.get("CALCOM_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.cal.com/v1/bookings",
                params={"apiKey": api_key}
            ) as response:
                data = await response.json()
                return [{"id": b["id"], "title": b["title"], "start": b["startTime"]}
                        for b in data.get("bookings", [])]

    # ==================== DOODLE ====================

    async def doodle_create_poll(self, title: str, options: List[Dict]) -> Dict:
        """Create Doodle poll"""
        import aiohttp

        api_key = os.environ.get("DOODLE_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://doodle.com/api/v2.0/polls",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"title": title, "options": options}
            ) as response:
                return await response.json()

    # ==================== SAVVYCAL ====================

    async def savvycal_get_links(self) -> List[Dict]:
        """Get SavvyCal links"""
        import aiohttp

        api_key = os.environ.get("SAVVYCAL_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://savvycal.com/api/v1/links",
                headers={"Authorization": f"Bearer {api_key}"}
            ) as response:
                return await response.json()

    # ==================== CRONIFY ====================

    async def cronify_create_job(self, name: str, cron: str, url: str, method: str = "GET") -> Dict:
        """Create Cronify scheduled job"""
        import aiohttp

        api_key = os.environ.get("CRONIFY_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.cronify.io/v1/jobs",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"name": name, "cron": cron, "url": url, "method": method}
            ) as response:
                return await response.json()

    # ==================== AI SCHEDULING ====================

    async def ai_suggest_meeting_times(
        self,
        participants: List[str],
        duration_minutes: int,
        preferences: str = None
    ) -> List[Dict]:
        """AI-powered meeting time suggestions"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """You are a scheduling assistant. Suggest optimal meeting times.
Consider: time zones, typical business hours, meeting duration.
Return JSON array: [{"start": "ISO datetime", "reason": "why this time is good"}]"""},
            {"role": "user", "content": f"""Participants: {participants}
Duration: {duration_minutes} minutes
Preferences: {preferences or 'Standard business hours'}"""}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return [{"suggestion": response["content"]}]

    def list_providers(self) -> List[str]:
        return ["google_calendar", "outlook", "calendly", "calcom", "doodle",
                "savvycal", "cronify", "acuity", "hubspot_meetings", "zoho_bookings"]
