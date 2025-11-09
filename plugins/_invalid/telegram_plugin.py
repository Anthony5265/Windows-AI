"""
Telegram Social Media Plugin
Supports bot commands and message handling for Telegram bots
"""

from typing import Dict, Any, Optional, List
import os
import asyncio


class TelegramPlugin:
    """Plugin for Telegram bot integration"""

    name = "telegram"
    version = "1.0.0"
    description = "Integration with Telegram Bot API for messaging and bot commands"
    author = "Windows AI Team"

    def __init__(self):
        self.bot_token: Optional[str] = None
        self.bot = None
        self._initialized = False
        self._loop = None
        self._handlers = {}

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Telegram plugin"""
        try:
            import telegram
            from telegram import Bot, Update
            from telegram.ext import Application, CommandHandler, MessageHandler, filters

            # Get bot token from config or environment
            self.bot_token = (
                config.get("bot_token") if config
                else os.getenv("TELEGRAM_BOT_TOKEN")
            )

            if not self.bot_token:
                return False

            # Create bot instance
            self.bot = Bot(token=self.bot_token)
            
            # Test bot connection
            bot_info = asyncio.run(self.bot.get_me())
            if not bot_info:
                return False

            self._initialized = True
            return True

        except ImportError:
            print("python-telegram-bot package not installed. Install with: pip install python-telegram-bot")
            return False
        except Exception as e:
            print(f"Error initializing Telegram plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Telegram action"""
        if not self._initialized:
            return {"error": "Plugin not initialized. Please provide Telegram bot token."}

        try:
            if action == "send_message":
                return self._send_message(params)
            elif action == "send_photo":
                return self._send_photo(params)
            elif action == "send_document":
                return self._send_document(params)
            elif action == "get_updates":
                return self._get_updates(params)
            elif action == "get_chat_info":
                return self._get_chat_info(params)
            elif action == "get_user_info":
                return self._get_user_info(params)
            elif action == "leave_chat":
                return self._leave_chat(params)
            elif action == "pin_message":
                return self._pin_message(params)
            elif action == "unpin_message":
                return self._unpin_message(params)
            elif action == "delete_message":
                return self._delete_message(params)
            elif action == "forward_message":
                return self._forward_message(params)
            elif action == "get_chat_members":
                return self._get_chat_members(params)
            elif action == "ban_user":
                return self._ban_user(params)
            elif action == "unban_user":
                return self._unban_user(params)
            elif action == "set_chat_title":
                return self._set_chat_title(params)
            elif action == "set_chat_description":
                return self._set_chat_description(params)
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
        """Send a message to a Telegram chat"""
        chat_id = params.get("chat_id")
        text = params.get("text", "")
        parse_mode = params.get("parse_mode", "HTML")  # HTML, Markdown, MarkdownV2
        disable_web_page_preview = params.get("disable_web_page_preview", False)
        disable_notification = params.get("disable_notification", False)
        reply_to_message_id = params.get("reply_to_message_id")

        if not chat_id or not text:
            return {"error": "chat_id and text are required"}

        async def send():
            try:
                message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=disable_web_page_preview,
                    disable_notification=disable_notification,
                    reply_to_message_id=reply_to_message_id
                )

                return {
                    "success": True,
                    "message_id": message.message_id,
                    "chat_id": message.chat.id,
                    "text": message.text,
                    "date": message.date.isoformat(),
                    "from_user": {
                        "id": message.from_user.id,
                        "username": message.from_user.username,
                        "first_name": message.from_user.first_name
                    } if message.from_user else None
                }
            except Exception as e:
                return {"error": f"Failed to send message: {str(e)}"}

        return self._run_async(send())

    def _send_photo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a photo to a Telegram chat"""
        chat_id = params.get("chat_id")
        photo = params.get("photo")  # Can be file path, URL, or file_id
        caption = params.get("caption", "")
        parse_mode = params.get("parse_mode", "HTML")
        disable_notification = params.get("disable_notification", False)

        if not chat_id or not photo:
            return {"error": "chat_id and photo are required"}

        async def send_photo():
            try:
                message = await self.bot.send_photo(
                    chat_id=chat_id,
                    photo=photo,
                    caption=caption,
                    parse_mode=parse_mode,
                    disable_notification=disable_notification
                )

                return {
                    "success": True,
                    "message_id": message.message_id,
                    "chat_id": message.chat.id,
                    "photo": {
                        "file_id": message.photo[-1].file_id,
                        "file_size": message.photo[-1].file_size,
                        "width": message.photo[-1].width,
                        "height": message.photo[-1].height
                    },
                    "caption": message.caption,
                    "date": message.date.isoformat()
                }
            except Exception as e:
                return {"error": f"Failed to send photo: {str(e)}"}

        return self._run_async(send_photo())

    def _send_document(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a document to a Telegram chat"""
        chat_id = params.get("chat_id")
        document = params.get("document")  # Can be file path, URL, or file_id
        caption = params.get("caption", "")
        parse_mode = params.get("parse_mode", "HTML")
        disable_notification = params.get("disable_notification", False)

        if not chat_id or not document:
            return {"error": "chat_id and document are required"}

        async def send_doc():
            try:
                message = await self.bot.send_document(
                    chat_id=chat_id,
                    document=document,
                    caption=caption,
                    parse_mode=parse_mode,
                    disable_notification=disable_notification
                )

                return {
                    "success": True,
                    "message_id": message.message_id,
                    "chat_id": message.chat.id,
                    "document": {
                        "file_id": message.document.file_id,
                        "file_name": message.document.file_name,
                        "file_size": message.document.file_size,
                        "mime_type": message.document.mime_type
                    },
                    "caption": message.caption,
                    "date": message.date.isoformat()
                }
            except Exception as e:
                return {"error": f"Failed to send document: {str(e)}"}

        return self._run_async(send_doc())

    def _get_updates(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get updates (messages) for the bot"""
        offset = params.get("offset", 0)
        limit = params.get("limit", 100)
        timeout = params.get("timeout", 0)
        allowed_updates = params.get("allowed_updates")

        if limit > 100:
            limit = 100  # Telegram API limit

        async def get_updates():
            try:
                updates = await self.bot.get_updates(
                    offset=offset,
                    limit=limit,
                    timeout=timeout,
                    allowed_updates=allowed_updates
                )

                result = []
                for update in updates:
                    result.append({
                        "update_id": update.update_id,
                        "message": {
                            "message_id": update.message.message_id,
                            "from_user": {
                                "id": update.message.from_user.id,
                                "username": update.message.from_user.username,
                                "first_name": update.message.from_user.first_name
                            } if update.message.from_user else None,
                            "chat": {
                                "id": update.message.chat.id,
                                "type": update.message.chat.type,
                                "title": getattr(update.message.chat, 'title', None)
                            },
                            "text": update.message.text,
                            "date": update.message.date.isoformat()
                        } if update.message else None,
                        "callback_query": {
                            "id": update.callback_query.id,
                            "from_user": {
                                "id": update.callback_query.from_user.id,
                                "username": update.callback_query.from_user.username
                            },
                            "message": update.callback_query.message.message_id if update.callback_query.message else None,
                            "data": update.callback_query.data
                        } if update.callback_query else None
                    })

                return {
                    "updates": result,
                    "count": len(result)
                }
            except Exception as e:
                return {"error": f"Failed to get updates: {str(e)}"}

        return self._run_async(get_updates())

    def _get_chat_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a Telegram chat"""
        chat_id = params.get("chat_id")

        if not chat_id:
            return {"error": "chat_id is required"}

        async def get_info():
            try:
                chat = await self.bot.get_chat(chat_id=chat_id)

                return {
                    "id": chat.id,
                    "type": chat.type,
                    "title": getattr(chat, 'title', None),
                    "username": getattr(chat, 'username', None),
                    "first_name": getattr(chat, 'first_name', None),
                    "description": getattr(chat, 'description', None),
                    "invite_link": getattr(chat, 'invite_link', None),
                    "pinned_message": chat.pinned_message.message_id if chat.pinned_message else None,
                    "permissions": getattr(chat, 'permissions', None).__dict__ if getattr(chat, 'permissions', None) else None
                }
            except Exception as e:
                return {"error": f"Failed to get chat info: {str(e)}"}

        return self._run_async(get_info())

    def _get_user_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a Telegram user"""
        user_id = params.get("user_id")

        if not user_id:
            return {"error": "user_id is required"}

        async def get_info():
            try:
                # Get user info from a chat or direct message
                # This is a simplified approach - in practice you might need to get this from updates
                chat_member = await self.bot.get_chat_member(chat_id=user_id, user_id=user_id)
                
                return {
                    "id": chat_member.user.id,
                    "username": chat_member.user.username,
                    "first_name": chat_member.user.first_name,
                    "last_name": chat_member.user.last_name,
                    "is_bot": chat_member.user.is_bot,
                    "language_code": getattr(chat_member.user, 'language_code', None),
                    "status": chat_member.status
                }
            except Exception as e:
                return {"error": f"Failed to get user info: {str(e)}"}

        return self._run_async(get_info())

    def _leave_chat(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Leave a Telegram chat"""
        chat_id = params.get("chat_id")

        if not chat_id:
            return {"error": "chat_id is required"}

        async def leave():
            try:
                await self.bot.leave_chat(chat_id=chat_id)
                return {
                    "success": True,
                    "chat_id": chat_id,
                    "left": True
                }
            except Exception as e:
                return {"error": f"Failed to leave chat: {str(e)}"}

        return self._run_async(leave())

    def _pin_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pin a message in a Telegram chat"""
        chat_id = params.get("chat_id")
        message_id = params.get("message_id")
        disable_notification = params.get("disable_notification", False)

        if not chat_id or not message_id:
            return {"error": "chat_id and message_id are required"}

        async def pin():
            try:
                await self.bot.pin_chat_message(
                    chat_id=chat_id,
                    message_id=message_id,
                    disable_notification=disable_notification
                )
                return {
                    "success": True,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "pinned": True
                }
            except Exception as e:
                return {"error": f"Failed to pin message: {str(e)}"}

        return self._run_async(pin())

    def _unpin_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unpin a message in a Telegram chat"""
        chat_id = params.get("chat_id")
        message_id = params.get("message_id")

        if not chat_id:
            return {"error": "chat_id is required"}

        async def unpin():
            try:
                if message_id:
                    await self.bot.unpin_chat_message(chat_id=chat_id, message_id=message_id)
                else:
                    await self.bot.unpin_all_chat_messages(chat_id=chat_id)
                
                return {
                    "success": True,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "unpinned": True
                }
            except Exception as e:
                return {"error": f"Failed to unpin message: {str(e)}"}

        return self._run_async(unpin())

    def _delete_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a message in a Telegram chat"""
        chat_id = params.get("chat_id")
        message_id = params.get("message_id")

        if not chat_id or not message_id:
            return {"error": "chat_id and message_id are required"}

        async def delete():
            try:
                await self.bot.delete_message(chat_id=chat_id, message_id=message_id)
                return {
                    "success": True,
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "deleted": True
                }
            except Exception as e:
                return {"error": f"Failed to delete message: {str(e)}"}

        return self._run_async(delete())

    def _forward_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Forward a message from one chat to another"""
        chat_id = params.get("chat_id")
        from_chat_id = params.get("from_chat_id")
        message_id = params.get("message_id")
        disable_notification = params.get("disable_notification", False)

        if not all([chat_id, from_chat_id, message_id]):
            return {"error": "chat_id, from_chat_id, and message_id are required"}

        async def forward():
            try:
                message = await self.bot.forward_message(
                    chat_id=chat_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                    disable_notification=disable_notification
                )

                return {
                    "success": True,
                    "message_id": message.message_id,
                    "chat_id": message.chat.id,
                    "date": message.date.isoformat(),
                    "forward_from": {
                        "id": message.forward_from.id,
                        "username": message.forward_from.username,
                        "first_name": message.forward_from.first_name
                    } if message.forward_from else None
                }
            except Exception as e:
                return {"error": f"Failed to forward message: {str(e)}"}

        return self._run_async(forward())

    def _get_chat_members(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get members of a Telegram chat"""
        chat_id = params.get("chat_id")
        limit = params.get("limit", 100)

        if not chat_id:
            return {"error": "chat_id is required"}

        if limit > 200:
            limit = 200  # Telegram API limit

        async def get_members():
            try:
                # This is a simplified approach - in practice you might need to use get_chat_administrators
                # or get_chat_member_count and then iterate through members
                admins = await self.bot.get_chat_administrators(chat_id=chat_id)
                
                members = []
                for admin in admins:
                    members.append({
                        "user": {
                            "id": admin.user.id,
                            "username": admin.user.username,
                            "first_name": admin.user.first_name,
                            "is_bot": admin.user.is_bot
                        },
                        "status": admin.status,
                        "custom_title": getattr(admin, 'custom_title', None),
                        "is_anonymous": getattr(admin, 'is_anonymous', False)
                    })

                return {
                    "members": members,
                    "count": len(members),
                    "chat_id": chat_id
                }
            except Exception as e:
                return {"error": f"Failed to get chat members: {str(e)}"}

        return self._run_async(get_members())

    def _ban_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ban a user from a Telegram chat"""
        chat_id = params.get("chat_id")
        user_id = params.get("user_id")
        until_date = params.get("until_date")  # Unix timestamp or None for permanent
        revoke_messages = params.get("revoke_messages", False)

        if not chat_id or not user_id:
            return {"error": "chat_id and user_id are required"}

        async def ban():
            try:
                await self.bot.ban_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    until_date=until_date,
                    revoke_messages=revoke_messages
                )
                return {
                    "success": True,
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "banned": True
                }
            except Exception as e:
                return {"error": f"Failed to ban user: {str(e)}"}

        return self._run_async(ban())

    def _unban_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Unban a user from a Telegram chat"""
        chat_id = params.get("chat_id")
        user_id = params.get("user_id")
        only_if_banned = params.get("only_if_banned", True)

        if not chat_id or not user_id:
            return {"error": "chat_id and user_id are required"}

        async def unban():
            try:
                await self.bot.unban_chat_member(
                    chat_id=chat_id,
                    user_id=user_id,
                    only_if_banned=only_if_banned
                )
                return {
                    "success": True,
                    "chat_id": chat_id,
                    "user_id": user_id,
                    "unbanned": True
                }
            except Exception as e:
                return {"error": f"Failed to unban user: {str(e)}"}

        return self._run_async(unban())

    def _set_chat_title(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set the title of a Telegram chat"""
        chat_id = params.get("chat_id")
        title = params.get("title", "")

        if not chat_id or not title:
            return {"error": "chat_id and title are required"}

        async def set_title():
            try:
                await self.bot.set_chat_title(chat_id=chat_id, title=title)
                return {
                    "success": True,
                    "chat_id": chat_id,
                    "title": title,
                    "updated": True
                }
            except Exception as e:
                return {"error": f"Failed to set chat title: {str(e)}"}

        return self._run_async(set_title())

    def _set_chat_description(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Set the description of a Telegram chat"""
        chat_id = params.get("chat_id")
        description = params.get("description", "")

        if not chat_id:
            return {"error": "chat_id is required"}

        async def set_description():
            try:
                await self.bot.set_chat_description(chat_id=chat_id, description=description)
                return {
                    "success": True,
                    "chat_id": chat_id,
                    "description": description,
                    "updated": True
                }
            except Exception as e:
                return {"error": f"Failed to set chat description: {str(e)}"}

        return self._run_async(set_description())

    def cleanup(self):
        """Cleanup resources"""
        if self._loop:
            self._loop.close()
        self.bot = None
        self._initialized = False


# Plugin metadata
PLUGIN_CLASS = TelegramPlugin
PLUGIN_NAME = "telegram"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Integration with Telegram Bot API for messaging and bot commands"
PLUGIN_ACTIONS = [
    "send_message", "send_photo", "send_document", "get_updates", "get_chat_info",
    "get_user_info", "leave_chat", "pin_message", "unpin_message", "delete_message",
    "forward_message", "get_chat_members", "ban_user", "unban_user", 
    "set_chat_title", "set_chat_description"
]