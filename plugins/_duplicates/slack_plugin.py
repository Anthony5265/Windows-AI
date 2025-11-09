"""
Slack Social Media Plugin
Supports messaging and workspace management for Slack integration
"""

from typing import Dict, Any, Optional, List
import os
import asyncio
import json
from datetime import datetime


class SlackPlugin:
    """Plugin for Slack API integration"""

    name = "slack"
    version = "1.0.0"
    description = "Integration with Slack API for messaging and workspace management"
    author = "Windows AI Team"

    def __init__(self):
        self.bot_token: Optional[str] = None
        self.user_token: Optional[str] = None
        self.client = None
        self._initialized = False
        self._loop = None

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Slack plugin"""
        try:
            from slack_sdk import WebClient
            from slack_sdk.errors import SlackApiError

            # Get tokens from config or environment
            if config:
                self.bot_token = config.get("bot_token") or os.getenv("SLACK_BOT_TOKEN")
                self.user_token = config.get("user_token") or os.getenv("SLACK_USER_TOKEN")
            else:
                self.bot_token = os.getenv("SLACK_BOT_TOKEN")
                self.user_token = os.getenv("SLACK_USER_TOKEN")

            if not self.bot_token and not self.user_token:
                print("No Slack tokens provided. Set SLACK_BOT_TOKEN or SLACK_USER_TOKEN environment variable.")
                return False

            # Create Slack client
            token = self.bot_token or self.user_token
            self.client = WebClient(token=token)

            # Test connection
            try:
                auth_response = self.client.auth_test()
                print(f"Connected to Slack as {auth_response['user']} in workspace {auth_response['team']}")
            except SlackApiError as e:
                print(f"Slack authentication failed: {e.response['error']}")
                return False

            self._initialized = True
            return True

        except ImportError:
            print("slack-sdk package not installed. Install with: pip install slack-sdk")
            return False
        except Exception as e:
            print(f"Error initializing Slack plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Slack action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide Slack token."}

        try:
            if action == "send_message":
                return self._send_message(params)
            elif action == "get_messages":
                return self._get_messages(params)
            elif action == "create_channel":
                return self._create_channel(params)
            elif action == "delete_channel":
                return self._delete_channel(params)
            elif action == "invite_to_channel":
                return self._invite_to_channel(params)
            elif action == "kick_from_channel":
                return self._kick_from_channel(params)
            elif action == "get_workspace_info":
                return self._get_workspace_info(params)
            elif action == "list_channels":
                return self._list_channels(params)
            elif action == "list_users":
                return self._list_users(params)
            elif action == "upload_file":
                return self._upload_file(params)
            elif action == "set_status":
                return self._set_status(params)
            elif action == "search_messages":
                return self._search_messages(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _send_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to a Slack channel or user"""
        channel = params.get("channel")
        message = params.get("message", "")
        thread_ts = params.get("thread_ts")  # For threaded replies

        if not channel or not message:
            return {"error": "channel and message are required"}

        try:
            message_params = {
                "channel": channel,
                "text": message
            }
            
            if thread_ts:
                message_params["thread_ts"] = thread_ts

            response = self.client.chat_postMessage(**message_params)
            
            return {
                "success": True,
                "message_id": response["ts"],
                "channel": response["channel"],
                "message": message,
                "timestamp": response["ts"],
                "thread_ts": response.get("thread_ts")
            }
        except Exception as e:
            return {"error": f"Failed to send message: {str(e)}"}

    def _get_messages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get messages from a Slack channel"""
        channel = params.get("channel")
        limit = params.get("limit", 10)
        oldest = params.get("oldest")  # Timestamp to start from
        latest = params.get("latest")  # Timestamp to end at

        if not channel:
            return {"error": "channel is required"}

        if limit > 100:
            limit = 100  # Slack API limit

        try:
            response = self.client.conversations_history(
                channel=channel,
                limit=limit,
                oldest=oldest,
                latest=latest
            )

            messages = []
            for msg in response["messages"]:
                messages.append({
                    "id": msg["ts"],
                    "text": msg.get("text", ""),
                    "user": msg.get("user"),
                    "bot_id": msg.get("bot_id"),
                    "timestamp": msg["ts"],
                    "thread_ts": msg.get("thread_ts"),
                    "reactions": msg.get("reactions", []),
                    "files": msg.get("files", []),
                    "reply_count": msg.get("reply_count", 0)
                })

            return {
                "messages": messages,
                "count": len(messages),
                "channel": channel,
                "has_more": response.get("has_more", False)
            }
        except Exception as e:
            return {"error": f"Failed to get messages: {str(e)}"}

    def _create_channel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Slack channel"""
        name = params.get("name", "")
        is_private = params.get("is_private", False)
        team_id = params.get("team_id")

        if not name:
            return {"error": "name is required"}

        try:
            if is_private:
                response = self.client.conversations_create(
                    name=name,
                    is_private=True,
                    team_id=team_id
                )
            else:
                response = self.client.conversations_create(
                    name=name,
                    is_private=False,
                    team_id=team_id
                )

            channel = response["channel"]
            
            return {
                "success": True,
                "channel_id": channel["id"],
                "channel_name": channel["name"],
                "is_private": channel["is_private"],
                "created": channel["created"],
                "creator": channel["creator"]
            }
        except Exception as e:
            return {"error": f"Failed to create channel: {str(e)}"}

    def _delete_channel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a Slack channel"""
        channel = params.get("channel")

        if not channel:
            return {"error": "channel is required"}

        try:
            response = self.client.conversations_delete(channel=channel)
            
            return {
                "success": True,
                "channel": channel,
                "deleted": True
            }
        except Exception as e:
            return {"error": f"Failed to delete channel: {str(e)}"}

    def _invite_to_channel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Invite users to a Slack channel"""
        channel = params.get("channel")
        users = params.get("users")  # Can be string (single user) or list

        if not channel or not users:
            return {"error": "channel and users are required"}

        if isinstance(users, str):
            users = [users]

        try:
            results = []
            for user in users:
                response = self.client.conversations_invite(
                    channel=channel,
                    users=user
                )
                results.append({
                    "user": user,
                    "invited": True
                })

            return {
                "success": True,
                "channel": channel,
                "invitations": results
            }
        except Exception as e:
            return {"error": f"Failed to invite users: {str(e)}"}

    def _kick_from_channel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove users from a Slack channel"""
        channel = params.get("channel")
        user = params.get("user")

        if not channel or not user:
            return {"error": "channel and user are required"}

        try:
            response = self.client.conversations_kick(
                channel=channel,
                user=user
            )
            
            return {
                "success": True,
                "channel": channel,
                "user": user,
                "removed": True
            }
        except Exception as e:
            return {"error": f"Failed to remove user: {str(e)}"}

    def _get_workspace_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about the Slack workspace"""
        team_id = params.get("team_id")

        try:
            if team_id:
                response = self.client.team_info(team=team_id)
            else:
                response = self.client.team_info()

            team = response["team"]
            
            return {
                "id": team["id"],
                "name": team["name"],
                "domain": team["domain"],
                "email_domain": team.get("email_domain"),
                "icon": team.get("icon", {}),
                "created": team["created"],
                "creator": team["creator"],
                "enterprise_id": team.get("enterprise_id"),
                "enterprise_name": team.get("enterprise_name"),
                "is_enterprise": team.get("is_enterprise", False)
            }
        except Exception as e:
            return {"error": f"Failed to get workspace info: {str(e)}"}

    def _list_channels(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List channels in the Slack workspace"""
        limit = params.get("limit", 100)
        exclude_archived = params.get("exclude_archived", True)
        types = params.get("types", "public_channel,private_channel")  # Channel types to include

        if limit > 1000:
            limit = 1000  # Slack API limit

        try:
            response = self.client.conversations_list(
                limit=limit,
                exclude_archived=exclude_archived,
                types=types
            )

            channels = []
            for channel in response["channels"]:
                channels.append({
                    "id": channel["id"],
                    "name": channel["name"],
                    "is_private": channel["is_private"],
                    "is_archived": channel["is_archived"],
                    "created": channel["created"],
                    "creator": channel["creator"],
                    "num_members": channel.get("num_members", 0),
                    "purpose": channel.get("purpose", {}).get("value", ""),
                    "topic": channel.get("topic", {}).get("value", "")
                })

            return {
                "channels": channels,
                "count": len(channels),
                "response_metadata": response.get("response_metadata", {})
            }
        except Exception as e:
            return {"error": f"Failed to list channels: {str(e)}"}

    def _list_users(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List users in the Slack workspace"""
        limit = params.get("limit", 100)
        presence = params.get("presence", False)  # Include presence info

        if limit > 1000:
            limit = 1000  # Slack API limit

        try:
            response = self.client.users_list(
                limit=limit,
                presence=presence
            )

            users = []
            for user in response["members"]:
                if not user["deleted"] and not user["is_bot"]:  # Skip deleted users and bots
                    users.append({
                        "id": user["id"],
                        "name": user["name"],
                        "real_name": user.get("real_name", ""),
                        "display_name": user["profile"].get("display_name", ""),
                        "email": user["profile"].get("email", ""),
                        "title": user["profile"].get("title", ""),
                        "phone": user["profile"].get("phone", ""),
                        "is_admin": user["is_admin"],
                        "is_owner": user["is_owner"],
                        "is_primary_owner": user["is_primary_owner"],
                        "presence": user.get("presence", "unknown") if presence else None,
                        "updated": user["updated"]
                    })

            return {
                "users": users,
                "count": len(users),
                "response_metadata": response.get("response_metadata", {})
            }
        except Exception as e:
            return {"error": f"Failed to list users: {str(e)}"}

    def _upload_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a file to a Slack channel"""
        channel = params.get("channel")
        file_path = params.get("file_path")
        title = params.get("title")
        initial_comment = params.get("initial_comment", "")

        if not channel or not file_path:
            return {"error": "channel and file_path are required"}

        try:
            response = self.client.files_upload_v2(
                channel=channel,
                file=file_path,
                title=title,
                initial_comment=initial_comment
            )

            file_info = response["file"]
            
            return {
                "success": True,
                "file_id": file_info["id"],
                "file_name": file_info["name"],
                "title": file_info.get("title", ""),
                "mimetype": file_info.get("mimetype", ""),
                "size": file_info.get("size", 0),
                "permalink": file_info.get("permalink", ""),
                "channel": channel
            }
        except Exception as e:
            return {"error": f"Failed to upload file: {str(e)}"}

    def _set_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set user status"""
        status_text = params.get("status_text", "")
        status_emoji = params.get("status_emoji", "")
        expiration = params.get("expiration")  # Unix timestamp

        try:
            response = self.client.users_profile_set(
                profile={
                    "status_text": status_text,
                    "status_emoji": status_emoji,
                    "status_expiration": expiration
                }
            )

            return {
                "success": True,
                "status_text": status_text,
                "status_emoji": status_emoji,
                "expiration": expiration
            }
        except Exception as e:
            return {"error": f"Failed to set status: {str(e)}"}

    def _search_messages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search for messages in the workspace"""
        query = params.get("query", "")
        count = params.get("count", 20)
        sort = params.get("sort", "timestamp")  # timestamp or relevance
        sort_dir = params.get("sort_dir", "desc")  # asc or desc

        if not query:
            return {"error": "query is required"}

        if count > 100:
            count = 100  # Slack API limit

        try:
            response = self.client.search_messages(
                query=query,
                count=count,
                sort=sort,
                sort_dir=sort_dir
            )

            messages = []
            for match in response["messages"]["matches"]:
                messages.append({
                    "id": match["ts"],
                    "text": match["text"],
                    "user": match["user"],
                    "username": match.get("username", ""),
                    "channel": match["channel"]["id"],
                    "channel_name": match["channel"]["name"],
                    "timestamp": match["ts"],
                    "permalink": match["permalink"],
                    "reactions": match.get("reactions", [])
                })

            return {
                "messages": messages,
                "count": len(messages),
                "query": query,
                "total": response["messages"]["pagination"]["total_count"]
            }
        except Exception as e:
            return {"error": f"Failed to search messages: {str(e)}"}

    def cleanup(self):
        """Cleanup resources"""
        self.client = None
        self._initialized = False
        if self._loop:
            self._loop.close()


# Plugin metadata
PLUGIN_CLASS = SlackPlugin
PLUGIN_NAME = "slack"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Slack API for messaging and workspace management"
PLUGIN_ACTIONS = [
    "send_message", "get_messages", "create_channel", "delete_channel",
    "invite_to_channel", "kick_from_channel", "get_workspace_info", 
    "list_channels", "list_users", "upload_file", "set_status", "search_messages"
]