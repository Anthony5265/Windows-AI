"""
Productivity Integrations Manager
20+ productivity tools and services
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
from datetime import datetime

logger = logging.getLogger(__name__)

class ProductivityManager:
    """Manages integrations with 20+ productivity services"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True
        logger.info("Productivity Manager initialized")

    # ==================== SLACK ====================

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

    async def slack_send_message(self, channel: str, text: str, **kwargs) -> Dict:
        """Send message to Slack channel"""
        from slack_sdk.web.async_client import AsyncWebClient

        client = AsyncWebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
        response = await client.chat_postMessage(
            channel=channel,
            text=text,
            **kwargs
        )
        return {"ok": response["ok"], "ts": response.get("ts")}

    async def slack_list_channels(self) -> List[Dict]:
        """List Slack channels"""
        from slack_sdk.web.async_client import AsyncWebClient

        client = AsyncWebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
        response = await client.conversations_list()
        return [{"id": c["id"], "name": c["name"]} for c in response["channels"]]

    # ==================== DISCORD ====================

    async def discord_send_message(self, channel_id: int, content: str) -> Dict:
        """Send message to Discord channel"""
        import aiohttp

        token = os.environ.get("DISCORD_BOT_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers={"Authorization": f"Bot {token}", "Content-Type": "application/json"},
                json={"content": content}
            ) as response:
                return await response.json()

    # ==================== NOTION ====================

    async def notion_create_page(self, parent_id: str, title: str, content: str) -> Dict:
        """Create a Notion page"""
        import aiohttp

        token = os.environ.get("NOTION_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.notion.com/v1/pages",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                },
                json={
                    "parent": {"page_id": parent_id},
                    "properties": {
                        "title": {"title": [{"text": {"content": title}}]}
                    },
                    "children": [
                        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": content}}]}}
                    ]
                }
            ) as response:
                return await response.json()

    async def notion_search(self, query: str) -> List[Dict]:
        """Search Notion"""
        import aiohttp

        token = os.environ.get("NOTION_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.notion.com/v1/search",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": "2022-06-28",
                    "Content-Type": "application/json"
                },
                json={"query": query}
            ) as response:
                data = await response.json()
                return data.get("results", [])

    # ==================== LINEAR ====================

    async def linear_create_issue(self, title: str, description: str, team_id: str) -> Dict:
        """Create a Linear issue"""
        import aiohttp

        token = os.environ.get("LINEAR_API_KEY")

        query = """
        mutation CreateIssue($title: String!, $description: String, $teamId: String!) {
            issueCreate(input: {title: $title, description: $description, teamId: $teamId}) {
                success
                issue { id title url }
            }
        }
        """

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.linear.app/graphql",
                headers={"Authorization": token, "Content-Type": "application/json"},
                json={"query": query, "variables": {"title": title, "description": description, "teamId": team_id}}
            ) as response:
                data = await response.json()
                return data.get("data", {}).get("issueCreate", {})

    # ==================== GITHUB ====================

    async def github_create_issue(self, owner: str, repo: str, title: str, body: str) -> Dict:
        """Create a GitHub issue"""
        import aiohttp

        token = os.environ.get("GITHUB_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.github.com/repos/{owner}/{repo}/issues",
                headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
                json={"title": title, "body": body}
            ) as response:
                return await response.json()

    async def github_list_repos(self, user: str = None) -> List[Dict]:
        """List GitHub repositories"""
        import aiohttp

        token = os.environ.get("GITHUB_TOKEN")
        url = f"https://api.github.com/users/{user}/repos" if user else "https://api.github.com/user/repos"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"Authorization": f"token {token}"}) as response:
                return await response.json()

    # ==================== GOOGLE WORKSPACE ====================

    async def google_create_doc(self, title: str) -> Dict:
        """Create a Google Doc"""
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(os.environ.get("GOOGLE_CREDENTIALS_PATH"))
        service = build("docs", "v1", credentials=creds)

        doc = service.documents().create(body={"title": title}).execute()
        return {"id": doc["documentId"], "title": doc["title"]}

    async def google_create_sheet(self, title: str) -> Dict:
        """Create a Google Sheet"""
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(os.environ.get("GOOGLE_CREDENTIALS_PATH"))
        service = build("sheets", "v4", credentials=creds)

        sheet = service.spreadsheets().create(body={"properties": {"title": title}}).execute()
        return {"id": sheet["spreadsheetId"], "url": sheet["spreadsheetUrl"]}

    async def gmail_send(self, to: str, subject: str, body: str) -> Dict:
        """Send email via Gmail"""
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        import base64
        from email.mime.text import MIMEText

        creds = Credentials.from_authorized_user_file(os.environ.get("GOOGLE_CREDENTIALS_PATH"))
        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {"id": result["id"]}

    # ==================== CALENDAR ====================

    async def google_calendar_create_event(
        self,
        title: str,
        start: datetime,
        end: datetime,
        description: str = None
    ) -> Dict:
        """Create Google Calendar event"""
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(os.environ.get("GOOGLE_CREDENTIALS_PATH"))
        service = build("calendar", "v3", credentials=creds)

        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"}
        }

        result = service.events().insert(calendarId="primary", body=event).execute()
        return {"id": result["id"], "link": result["htmlLink"]}

    # ==================== TODOIST ====================

    async def todoist_create_task(self, content: str, due: str = None, priority: int = 1) -> Dict:
        """Create Todoist task"""
        import aiohttp

        token = os.environ.get("TODOIST_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.todoist.com/rest/v2/tasks",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"content": content, "due_string": due, "priority": priority}
            ) as response:
                return await response.json()

    async def todoist_list_tasks(self) -> List[Dict]:
        """List Todoist tasks"""
        import aiohttp

        token = os.environ.get("TODOIST_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.todoist.com/rest/v2/tasks",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                return await response.json()

    # ==================== AIRTABLE ====================

    async def airtable_list_records(self, base_id: str, table_name: str) -> List[Dict]:
        """List Airtable records"""
        import aiohttp

        token = os.environ.get("AIRTABLE_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.airtable.com/v0/{base_id}/{table_name}",
                headers={"Authorization": f"Bearer {token}"}
            ) as response:
                data = await response.json()
                return data.get("records", [])

    async def airtable_create_record(self, base_id: str, table_name: str, fields: Dict) -> Dict:
        """Create Airtable record"""
        import aiohttp

        token = os.environ.get("AIRTABLE_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.airtable.com/v0/{base_id}/{table_name}",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"fields": fields}
            ) as response:
                return await response.json()

    # ==================== TRELLO ====================

    async def trello_create_card(self, list_id: str, name: str, desc: str = None) -> Dict:
        """Create Trello card"""
        import aiohttp

        key = os.environ.get("TRELLO_API_KEY")
        token = os.environ.get("TRELLO_TOKEN")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.trello.com/1/cards",
                params={"key": key, "token": token, "idList": list_id, "name": name, "desc": desc}
            ) as response:
                return await response.json()
