"""
Slack Enhanced Plugin
Full-featured Slack integration with official SDK
"""
from typing import Dict, Any, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_SDK_AVAILABLE = True
except ImportError:
    SLACK_SDK_AVAILABLE = False
    logger.warning("slack-sdk not installed. Install with: pip install slack-sdk")


class Plugin:
    """Enhanced Slack plugin with full SDK integration"""

    def __init__(self):
        self.name = "Slack Enhanced"
        self.version = "2.0.0"
        self.description = "Full Slack integration: messages, channels, files, users, search"

        # Configuration
        self.token = os.getenv("SLACK_BOT_TOKEN", os.getenv("SLACK_TOKEN", ""))
        self.client: Optional[WebClient] = None

        # Initialize client
        if SLACK_SDK_AVAILABLE and self.token:
            try:
                self.client = WebClient(token=self.token)
                logger.info("Slack client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Slack client: {e}")

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute Slack operation

        Args:
            action (str): Action to perform
            **kwargs: Additional parameters

        Returns:
            Dict with status and results
        """
        if not SLACK_SDK_AVAILABLE:
            return {
                "status": "error",
                "message": "slack-sdk not installed. Install with: pip install slack-sdk"
            }

        if not self.token or not self.client:
            return {
                "status": "error",
                "message": "Slack token not configured. Set SLACK_BOT_TOKEN environment variable."
            }

        try:
            action = kwargs.get("action", "send_message")

            # Route to appropriate handler
            if action == "send_message":
                return await self._send_message(**kwargs)
            elif action == "get_messages":
                return await self._get_messages(**kwargs)
            elif action == "update_message":
                return await self._update_message(**kwargs)
            elif action == "delete_message":
                return await self._delete_message(**kwargs)
            elif action == "list_channels":
                return await self._list_channels(**kwargs)
            elif action == "create_channel":
                return await self._create_channel(**kwargs)
            elif action == "join_channel":
                return await self._join_channel(**kwargs)
            elif action == "leave_channel":
                return await self._leave_channel(**kwargs)
            elif action == "upload_file":
                return await self._upload_file(**kwargs)
            elif action == "list_users":
                return await self._list_users(**kwargs)
            elif action == "get_user":
                return await self._get_user(**kwargs)
            elif action == "search":
                return await self._search(**kwargs)
            elif action == "set_status":
                return await self._set_status(**kwargs)
            elif action == "get_permalink":
                return await self._get_permalink(**kwargs)
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return {
                "status": "error",
                "message": e.response.get('error', str(e)),
                "error_code": e.response.get('error')
            }
        except Exception as e:
            logger.error(f"Slack error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def _send_message(self, **kwargs) -> Dict[str, Any]:
        """Send a message to a channel or user"""
        channel = kwargs.get("channel", "")
        text = kwargs.get("text", kwargs.get("message", ""))
        thread_ts = kwargs.get("thread_ts", None)
        blocks = kwargs.get("blocks", None)
        attachments = kwargs.get("attachments", None)

        response = self.client.chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts,
            blocks=blocks,
            attachments=attachments
        )

        return {
            "status": "success",
            "message_ts": response["ts"],
            "channel": response["channel"],
            "message": response.get("message", {})
        }

    async def _get_messages(self, **kwargs) -> Dict[str, Any]:
        """Get messages from a channel"""
        channel = kwargs.get("channel", "")
        limit = kwargs.get("limit", 100)
        oldest = kwargs.get("oldest", None)
        latest = kwargs.get("latest", None)

        response = self.client.conversations_history(
            channel=channel,
            limit=limit,
            oldest=oldest,
            latest=latest
        )

        messages = []
        for msg in response["messages"]:
            messages.append({
                "ts": msg.get("ts"),
                "user": msg.get("user"),
                "text": msg.get("text"),
                "type": msg.get("type"),
                "thread_ts": msg.get("thread_ts")
            })

        return {
            "status": "success",
            "messages": messages,
            "has_more": response.get("has_more", False)
        }

    async def _update_message(self, **kwargs) -> Dict[str, Any]:
        """Update an existing message"""
        channel = kwargs.get("channel", "")
        ts = kwargs.get("ts", kwargs.get("message_ts", ""))
        text = kwargs.get("text", "")
        blocks = kwargs.get("blocks", None)

        response = self.client.chat_update(
            channel=channel,
            ts=ts,
            text=text,
            blocks=blocks
        )

        return {
            "status": "success",
            "ts": response["ts"],
            "channel": response["channel"]
        }

    async def _delete_message(self, **kwargs) -> Dict[str, Any]:
        """Delete a message"""
        channel = kwargs.get("channel", "")
        ts = kwargs.get("ts", kwargs.get("message_ts", ""))

        response = self.client.chat_delete(
            channel=channel,
            ts=ts
        )

        return {
            "status": "success",
            "ts": response["ts"],
            "channel": response["channel"]
        }

    async def _list_channels(self, **kwargs) -> Dict[str, Any]:
        """List all channels"""
        types = kwargs.get("types", "public_channel,private_channel")
        limit = kwargs.get("limit", 100)
        exclude_archived = kwargs.get("exclude_archived", True)

        response = self.client.conversations_list(
            types=types,
            limit=limit,
            exclude_archived=exclude_archived
        )

        channels = []
        for channel in response["channels"]:
            channels.append({
                "id": channel["id"],
                "name": channel["name"],
                "is_private": channel.get("is_private", False),
                "is_member": channel.get("is_member", False),
                "num_members": channel.get("num_members", 0)
            })

        return {
            "status": "success",
            "channels": channels
        }

    async def _create_channel(self, **kwargs) -> Dict[str, Any]:
        """Create a new channel"""
        name = kwargs.get("name", "")
        is_private = kwargs.get("is_private", False)

        response = self.client.conversations_create(
            name=name,
            is_private=is_private
        )

        channel = response["channel"]
        return {
            "status": "success",
            "channel": {
                "id": channel["id"],
                "name": channel["name"],
                "is_private": channel.get("is_private", False)
            }
        }

    async def _join_channel(self, **kwargs) -> Dict[str, Any]:
        """Join a channel"""
        channel = kwargs.get("channel", "")

        response = self.client.conversations_join(
            channel=channel
        )

        return {
            "status": "success",
            "channel": response["channel"]["id"]
        }

    async def _leave_channel(self, **kwargs) -> Dict[str, Any]:
        """Leave a channel"""
        channel = kwargs.get("channel", "")

        self.client.conversations_leave(
            channel=channel
        )

        return {
            "status": "success",
            "channel": channel
        }

    async def _upload_file(self, **kwargs) -> Dict[str, Any]:
        """Upload a file"""
        channels = kwargs.get("channels", kwargs.get("channel", ""))
        file = kwargs.get("file", "")
        filename = kwargs.get("filename", "file.txt")
        title = kwargs.get("title", None)
        initial_comment = kwargs.get("initial_comment", None)

        response = self.client.files_upload_v2(
            channels=channels,
            file=file,
            filename=filename,
            title=title,
            initial_comment=initial_comment
        )

        file_info = response["file"]
        return {
            "status": "success",
            "file": {
                "id": file_info["id"],
                "name": file_info["name"],
                "url": file_info.get("url_private", ""),
                "size": file_info.get("size", 0)
            }
        }

    async def _list_users(self, **kwargs) -> Dict[str, Any]:
        """List all users"""
        limit = kwargs.get("limit", 100)

        response = self.client.users_list(
            limit=limit
        )

        users = []
        for user in response["members"]:
            if not user.get("deleted", False):
                users.append({
                    "id": user["id"],
                    "name": user.get("name", ""),
                    "real_name": user.get("real_name", ""),
                    "is_bot": user.get("is_bot", False),
                    "is_admin": user.get("is_admin", False)
                })

        return {
            "status": "success",
            "users": users
        }

    async def _get_user(self, **kwargs) -> Dict[str, Any]:
        """Get user information"""
        user_id = kwargs.get("user_id", kwargs.get("user", ""))

        response = self.client.users_info(
            user=user_id
        )

        user = response["user"]
        return {
            "status": "success",
            "user": {
                "id": user["id"],
                "name": user.get("name", ""),
                "real_name": user.get("real_name", ""),
                "email": user.get("profile", {}).get("email", ""),
                "title": user.get("profile", {}).get("title", ""),
                "is_bot": user.get("is_bot", False),
                "is_admin": user.get("is_admin", False)
            }
        }

    async def _search(self, **kwargs) -> Dict[str, Any]:
        """Search messages"""
        query = kwargs.get("query", "")
        count = kwargs.get("count", 20)

        response = self.client.search_messages(
            query=query,
            count=count
        )

        matches = []
        for match in response["messages"]["matches"]:
            matches.append({
                "text": match.get("text", ""),
                "user": match.get("username", ""),
                "channel": match.get("channel", {}).get("name", ""),
                "ts": match.get("ts", ""),
                "permalink": match.get("permalink", "")
            })

        return {
            "status": "success",
            "matches": matches,
            "total": response["messages"].get("total", 0)
        }

    async def _set_status(self, **kwargs) -> Dict[str, Any]:
        """Set user status"""
        status_text = kwargs.get("status_text", "")
        status_emoji = kwargs.get("status_emoji", ":robot_face:")
        status_expiration = kwargs.get("status_expiration", 0)

        response = self.client.users_profile_set(
            profile={
                "status_text": status_text,
                "status_emoji": status_emoji,
                "status_expiration": status_expiration
            }
        )

        return {
            "status": "success",
            "profile": response["profile"]
        }

    async def _get_permalink(self, **kwargs) -> Dict[str, Any]:
        """Get permalink for a message"""
        channel = kwargs.get("channel", "")
        message_ts = kwargs.get("message_ts", kwargs.get("ts", ""))

        response = self.client.chat_getPermalink(
            channel=channel,
            message_ts=message_ts
        )

        return {
            "status": "success",
            "permalink": response["permalink"]
        }
