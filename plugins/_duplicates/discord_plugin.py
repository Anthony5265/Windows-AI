"""
Discord Social Media Plugin
Supports messages and server management for Discord bots
"""

from typing import Dict, Any, Optional, List
import os
import asyncio


class DiscordPlugin:
    """Plugin for Discord bot integration"""

    name = "discord"
    version = "1.0.0"
    description = "Integration with Discord API for bot messaging and server management"
    author = "Windows AI Team"

    def __init__(self):
        self.bot_token: Optional[str] = None
        self.client = None
        self._initialized = False
        self._loop = None

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Discord plugin"""
        try:
            import discord
            from discord.ext import commands

            # Get bot token from config or environment
            self.bot_token = (
                config.get("bot_token") if config
                else os.getenv("DISCORD_BOT_TOKEN")
            )

            if not self.bot_token:
                return False

            # Create bot client
            intents = discord.Intents.default()
            intents.message_content = True
            intents.members = True
            intents.guilds = True

            self.client = commands.Bot(command_prefix='!', intents=intents)

            # Set up event handlers
            @self.client.event
            async def on_ready():
                print(f'Discord bot logged in as {self.client.user}')

            @self.client.event
            async def on_message(message):
                # Process commands
                await self.client.process_commands(message)

            self._initialized = True
            return True

        except ImportError:
            print("discord.py package not installed. Install with: pip install discord.py")
            return False
        except Exception as e:
            print(f"Error initializing Discord plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Discord action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide Discord bot token."}

        try:
            if action == "send_message":
                return self._send_message(params)
            elif action == "get_messages":
                return self._get_messages(params)
            elif action == "create_channel":
                return self._create_channel(params)
            elif action == "delete_channel":
                return self._delete_channel(params)
            elif action == "create_role":
                return self._create_role(params)
            elif action == "assign_role":
                return self._assign_role(params)
            elif action == "get_server_info":
                return self._get_server_info(params)
            elif action == "list_channels":
                return self._list_channels(params)
            elif action == "list_members":
                return self._list_members(params)
            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            return {"error": str(e)}

    def _run_async(self, coro):
        """Run an async coroutine in the event loop"""
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)

        return self._loop.run_until_complete(coro)

    def _send_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to a Discord channel"""
        channel_id = params.get("channel_id")
        message = params.get("message", "")

        if not channel_id or not message:
            return {"error": "channel_id and message are required"}

        async def send():
            try:
                channel = self.client.get_channel(int(channel_id))
                if not channel:
                    return {"error": "Channel not found"}

                sent_message = await channel.send(message)
                return {
                    "success": True,
                    "message_id": sent_message.id,
                    "channel_id": sent_message.channel.id,
                    "content": sent_message.content,
                    "timestamp": sent_message.created_at.isoformat()
                }
            except Exception as e:
                return {"error": f"Failed to send message: {str(e)}"}

        return self._run_async(send())

    def _get_messages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get messages from a Discord channel"""
        channel_id = params.get("channel_id")
        limit = params.get("limit", 10)

        if not channel_id:
            return {"error": "channel_id is required"}

        if limit > 100:
            limit = 100  # Discord API limit

        async def get_msgs():
            try:
                channel = self.client.get_channel(int(channel_id))
                if not channel:
                    return {"error": "Channel not found"}

                messages = []
                async for message in channel.history(limit=limit):
                    messages.append({
                        "id": message.id,
                        "content": message.content,
                        "author": {
                            "id": message.author.id,
                            "name": message.author.name,
                            "discriminator": message.author.discriminator
                        },
                        "timestamp": message.created_at.isoformat(),
                        "attachments": len(message.attachments),
                        "embeds": len(message.embeds)
                    })

                return {
                    "messages": messages,
                    "count": len(messages),
                    "channel_id": channel_id
                }
            except Exception as e:
                return {"error": f"Failed to get messages: {str(e)}"}

        return self._run_async(get_msgs())

    def _create_channel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new channel in a Discord server"""
        guild_id = params.get("guild_id")
        channel_name = params.get("name", "")
        channel_type = params.get("type", "text")  # text, voice, category

        if not guild_id or not channel_name:
            return {"error": "guild_id and name are required"}

        async def create():
            try:
                guild = self.client.get_guild(int(guild_id))
                if not guild:
                    return {"error": "Guild not found"}

                if channel_type == "text":
                    channel = await guild.create_text_channel(channel_name)
                elif channel_type == "voice":
                    channel = await guild.create_voice_channel(channel_name)
                elif channel_type == "category":
                    channel = await guild.create_category_channel(channel_name)
                else:
                    return {"error": "Invalid channel type. Use: text, voice, or category"}

                return {
                    "success": True,
                    "channel_id": channel.id,
                    "channel_name": channel.name,
                    "channel_type": str(channel.type),
                    "guild_id": guild.id
                }
            except Exception as e:
                return {"error": f"Failed to create channel: {str(e)}"}

        return self._run_async(create())

    def _delete_channel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a Discord channel"""
        channel_id = params.get("channel_id")

        if not channel_id:
            return {"error": "channel_id is required"}

        async def delete():
            try:
                channel = self.client.get_channel(int(channel_id))
                if not channel:
                    return {"error": "Channel not found"}

                await channel.delete()
                return {
                    "success": True,
                    "channel_id": channel_id,
                    "deleted": True
                }
            except Exception as e:
                return {"error": f"Failed to delete channel: {str(e)}"}

        return self._run_async(delete())

    def _create_role(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new role in a Discord server"""
        guild_id = params.get("guild_id")
        role_name = params.get("name", "")
        color = params.get("color", 0x000000)  # Hex color
        permissions = params.get("permissions", 0)  # Permission integer

        if not guild_id or not role_name:
            return {"error": "guild_id and name are required"}

        async def create():
            try:
                guild = self.client.get_guild(int(guild_id))
                if not guild:
                    return {"error": "Guild not found"}

                role = await guild.create_role(
                    name=role_name,
                    color=color,
                    permissions=discord.Permissions(permissions=permissions)
                )

                return {
                    "success": True,
                    "role_id": role.id,
                    "role_name": role.name,
                    "color": role.color.value,
                    "guild_id": guild.id
                }
            except Exception as e:
                return {"error": f"Failed to create role: {str(e)}"}

        return self._run_async(create())

    def _assign_role(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Assign a role to a member"""
        guild_id = params.get("guild_id")
        user_id = params.get("user_id")
        role_id = params.get("role_id")

        if not all([guild_id, user_id, role_id]):
            return {"error": "guild_id, user_id, and role_id are required"}

        async def assign():
            try:
                guild = self.client.get_guild(int(guild_id))
                if not guild:
                    return {"error": "Guild not found"}

                member = guild.get_member(int(user_id))
                if not member:
                    return {"error": "Member not found"}

                role = guild.get_role(int(role_id))
                if not role:
                    return {"error": "Role not found"}

                await member.add_roles(role)
                return {
                    "success": True,
                    "user_id": user_id,
                    "role_id": role_id,
                    "guild_id": guild_id
                }
            except Exception as e:
                return {"error": f"Failed to assign role: {str(e)}"}

        return self._run_async(assign())

    def _get_server_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a Discord server"""
        guild_id = params.get("guild_id")

        if not guild_id:
            return {"error": "guild_id is required"}

        async def get_info():
            try:
                guild = self.client.get_guild(int(guild_id))
                if not guild:
                    return {"error": "Guild not found"}

                return {
                    "id": guild.id,
                    "name": guild.name,
                    "owner_id": guild.owner_id,
                    "member_count": guild.member_count,
                    "channel_count": len(guild.channels),
                    "role_count": len(guild.roles),
                    "created_at": guild.created_at.isoformat(),
                    "description": guild.description
                }
            except Exception as e:
                return {"error": f"Failed to get server info: {str(e)}"}

        return self._run_async(get_info())

    def _list_channels(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List channels in a Discord server"""
        guild_id = params.get("guild_id")

        if not guild_id:
            return {"error": "guild_id is required"}

        async def list_ch():
            try:
                guild = self.client.get_guild(int(guild_id))
                if not guild:
                    return {"error": "Guild not found"}

                channels = []
                for channel in guild.channels:
                    channels.append({
                        "id": channel.id,
                        "name": channel.name,
                        "type": str(channel.type),
                        "position": channel.position
                    })

                return {
                    "channels": channels,
                    "count": len(channels),
                    "guild_id": guild_id
                }
            except Exception as e:
                return {"error": f"Failed to list channels: {str(e)}"}

        return self._run_async(list_ch())

    def _list_members(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List members in a Discord server"""
        guild_id = params.get("guild_id")
        limit = params.get("limit", 100)

        if not guild_id:
            return {"error": "guild_id is required"}

        if limit > 1000:
            limit = 1000  # Discord API limit

        async def list_mem():
            try:
                guild = self.client.get_guild(int(guild_id))
                if not guild:
                    return {"error": "Guild not found"}

                members = []
                async for member in guild.fetch_members(limit=limit):
                    members.append({
                        "id": member.id,
                        "name": member.name,
                        "discriminator": member.discriminator,
                        "nick": member.nick,
                        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
                        "roles": [role.id for role in member.roles]
                    })

                return {
                    "members": members,
                    "count": len(members),
                    "guild_id": guild_id
                }
            except Exception as e:
                return {"error": f"Failed to list members: {str(e)}"}

        return self._run_async(list_mem())

    def cleanup(self):
        """Cleanup resources"""
        if self._loop:
            self._loop.close()
        self.client = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = DiscordPlugin
PLUGIN_NAME = "discord"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Discord API for bot messaging and server management"
PLUGIN_ACTIONS = [
    "send_message", "get_messages", "create_channel", "delete_channel",
    "create_role", "assign_role", "get_server_info", "list_channels", "list_members"
]