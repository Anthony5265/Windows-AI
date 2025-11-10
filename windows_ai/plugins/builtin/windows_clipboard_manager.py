"""
Windows Clipboard Manager Plugin
Advanced clipboard history tracking and management

Features:
- Clipboard history with configurable size
- Multiple clipboard item types (text, images, files)
- Search and filter clipboard history
- Pin favorite items
- Clipboard synchronization
- Export/import clipboard history
- Smart paste suggestions

Author: Windows AI Team
Version: 1.0.0
"""

from typing import Dict, Any, List, Optional
import logging
import asyncio
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib
import json
from pathlib import Path

from windows_ai.plugins.base import ToolPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


@dataclass
class ClipboardItem:
    """Represents a clipboard history item"""
    id: str
    content: str
    content_type: str  # text, image, file, html
    timestamp: str
    source_app: Optional[str] = None
    pinned: bool = False
    tags: List[str] = None
    preview: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.preview is None and self.content_type == "text":
            self.preview = self.content[:100] if len(self.content) > 100 else self.content


class WindowsClipboardManagerPlugin(ToolPlugin):
    """Advanced clipboard management with history and search"""

    def __init__(self):
        metadata = PluginMetadata(
            id="windows_clipboard_manager",
            name="Windows Clipboard Manager",
            description="Advanced clipboard history tracking with search, pin, and sync features",
            version="1.0.0",
            author="Windows AI Team",
            plugin_type=PluginType.TOOL,
            enabled=True,
            icon="📋",
            tags=["clipboard", "history", "windows", "productivity"],
            requirements=["pyperclip>=1.8.0"]
        )
        super().__init__(metadata)

        # Configuration
        self.max_history_size = 1000
        self.auto_capture = True
        self.capture_interval = 1.0  # seconds

        # State
        self.clipboard_history: List[ClipboardItem] = []
        self.pinned_items: List[ClipboardItem] = []
        self.current_clipboard: Optional[str] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize clipboard manager"""
        try:
            # Try to import clipboard libraries
            try:
                import pyperclip
                self.pyperclip = pyperclip
                logger.info("✓ Clipboard library loaded (pyperclip)")
            except ImportError:
                logger.warning("⚠ pyperclip not available, using fallback clipboard")
                self.pyperclip = None

            # Load history from disk if available
            await self._load_history()

            # Start monitoring if auto-capture is enabled
            if self.auto_capture:
                await self._start_monitoring()

            self._initialized = True
            logger.info("✓ Clipboard manager initialized")
            return True

        except Exception as e:
            logger.error(f"Error initializing clipboard manager: {e}")
            return False

    async def shutdown(self):
        """Cleanup clipboard manager"""
        try:
            # Stop monitoring
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            # Save history
            await self._save_history()

            logger.info("Clipboard manager shut down")

        except Exception as e:
            logger.error(f"Error shutting down clipboard manager: {e}")

    async def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute clipboard operations

        Args:
            query: Action to perform
            parameters: Action-specific parameters
        """
        try:
            params = parameters or {}
            params.update(kwargs)

            # Action routing
            actions = {
                "get_history": self._get_history,
                "get_current": self._get_current,
                "set_clipboard": self._set_clipboard,
                "search": self._search,
                "pin": self._pin_item,
                "unpin": self._unpin_item,
                "get_pinned": self._get_pinned,
                "delete": self._delete_item,
                "clear_history": self._clear_history,
                "export": self._export_history,
                "import": self._import_history,
                "start_monitoring": self._start_monitoring,
                "stop_monitoring": self._stop_monitoring,
                "get_stats": self._get_stats,
            }

            action = query.lower().replace(" ", "_")

            if action not in actions:
                # Try to match partial action names
                matching = [a for a in actions.keys() if action in a]
                if len(matching) == 1:
                    action = matching[0]
                else:
                    return {
                        "success": False,
                        "error": f"Unknown action: {query}",
                        "available_actions": list(actions.keys())
                    }

            handler = actions[action]
            result = await handler(**params)

            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            logger.error(f"Clipboard manager error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for parameters"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "get_history", "get_current", "set_clipboard",
                        "search", "pin", "unpin", "get_pinned",
                        "delete", "clear_history", "export", "import",
                        "start_monitoring", "stop_monitoring", "get_stats"
                    ],
                    "description": "Action to perform"
                },
                "content": {
                    "type": "string",
                    "description": "Content for set_clipboard action"
                },
                "item_id": {
                    "type": "string",
                    "description": "Item ID for pin/unpin/delete actions"
                },
                "search_query": {
                    "type": "string",
                    "description": "Search query for search action"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of items to return",
                    "default": 50
                },
                "file_path": {
                    "type": "string",
                    "description": "File path for export/import actions"
                }
            },
            "required": ["action"]
        }

    # =========================================================================
    # Clipboard Operations
    # =========================================================================

    async def _get_current(self, **kwargs) -> Dict[str, Any]:
        """Get current clipboard content"""
        try:
            if self.pyperclip:
                content = self.pyperclip.paste()
            else:
                content = self.current_clipboard or ""

            return {
                "content": content,
                "content_type": "text",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "error": f"Failed to get clipboard: {str(e)}",
                "content": ""
            }

    async def _set_clipboard(self, content: str, **kwargs) -> Dict[str, Any]:
        """Set clipboard content"""
        try:
            if self.pyperclip:
                self.pyperclip.copy(content)
            else:
                self.current_clipboard = content

            # Add to history
            await self._add_to_history(content, "text")

            return {
                "success": True,
                "message": "Clipboard updated",
                "content_length": len(content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to set clipboard: {str(e)}"
            }

    async def _get_history(self, limit: int = 50, **kwargs) -> Dict[str, Any]:
        """Get clipboard history"""
        items = self.clipboard_history[:limit]

        return {
            "items": [asdict(item) for item in items],
            "total_count": len(self.clipboard_history),
            "returned_count": len(items)
        }

    async def _search(self, search_query: str, limit: int = 50, **kwargs) -> Dict[str, Any]:
        """Search clipboard history"""
        query_lower = search_query.lower()

        matching_items = [
            item for item in self.clipboard_history
            if query_lower in item.content.lower()
            or any(query_lower in tag.lower() for tag in item.tags)
        ][:limit]

        return {
            "items": [asdict(item) for item in matching_items],
            "query": search_query,
            "matches_found": len(matching_items)
        }

    # =========================================================================
    # Pin Management
    # =========================================================================

    async def _pin_item(self, item_id: str, **kwargs) -> Dict[str, Any]:
        """Pin a clipboard item"""
        for item in self.clipboard_history:
            if item.id == item_id:
                item.pinned = True
                if item not in self.pinned_items:
                    self.pinned_items.append(item)

                await self._save_history()

                return {
                    "success": True,
                    "message": f"Item pinned: {item.preview}"
                }

        return {
            "success": False,
            "error": f"Item not found: {item_id}"
        }

    async def _unpin_item(self, item_id: str, **kwargs) -> Dict[str, Any]:
        """Unpin a clipboard item"""
        for item in self.clipboard_history:
            if item.id == item_id:
                item.pinned = False
                if item in self.pinned_items:
                    self.pinned_items.remove(item)

                await self._save_history()

                return {
                    "success": True,
                    "message": f"Item unpinned: {item.preview}"
                }

        return {
            "success": False,
            "error": f"Item not found: {item_id}"
        }

    async def _get_pinned(self, **kwargs) -> Dict[str, Any]:
        """Get all pinned items"""
        return {
            "items": [asdict(item) for item in self.pinned_items],
            "count": len(self.pinned_items)
        }

    # =========================================================================
    # History Management
    # =========================================================================

    async def _delete_item(self, item_id: str, **kwargs) -> Dict[str, Any]:
        """Delete an item from history"""
        for i, item in enumerate(self.clipboard_history):
            if item.id == item_id:
                deleted_item = self.clipboard_history.pop(i)

                if deleted_item in self.pinned_items:
                    self.pinned_items.remove(deleted_item)

                await self._save_history()

                return {
                    "success": True,
                    "message": f"Item deleted: {deleted_item.preview}"
                }

        return {
            "success": False,
            "error": f"Item not found: {item_id}"
        }

    async def _clear_history(self, keep_pinned: bool = True, **kwargs) -> Dict[str, Any]:
        """Clear clipboard history"""
        original_count = len(self.clipboard_history)

        if keep_pinned:
            self.clipboard_history = [item for item in self.clipboard_history if item.pinned]
            cleared_count = original_count - len(self.clipboard_history)
        else:
            self.clipboard_history.clear()
            self.pinned_items.clear()
            cleared_count = original_count

        await self._save_history()

        return {
            "success": True,
            "message": f"Cleared {cleared_count} items",
            "remaining": len(self.clipboard_history)
        }

    # =========================================================================
    # Monitoring
    # =========================================================================

    async def _start_monitoring(self, **kwargs) -> Dict[str, Any]:
        """Start monitoring clipboard for changes"""
        if self.monitoring_task and not self.monitoring_task.done():
            return {
                "success": False,
                "message": "Monitoring already active"
            }

        self.auto_capture = True
        self.monitoring_task = asyncio.create_task(self._monitor_clipboard())

        return {
            "success": True,
            "message": "Clipboard monitoring started"
        }

    async def _stop_monitoring(self, **kwargs) -> Dict[str, Any]:
        """Stop monitoring clipboard"""
        self.auto_capture = False

        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        return {
            "success": True,
            "message": "Clipboard monitoring stopped"
        }

    async def _monitor_clipboard(self):
        """Background task to monitor clipboard changes"""
        last_content = None

        while self.auto_capture:
            try:
                current_result = await self._get_current()
                current_content = current_result.get("content", "")

                if current_content and current_content != last_content:
                    await self._add_to_history(current_content, "text")
                    last_content = current_content

                await asyncio.sleep(self.capture_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring clipboard: {e}")
                await asyncio.sleep(self.capture_interval)

    async def _add_to_history(self, content: str, content_type: str):
        """Add item to clipboard history"""
        # Generate ID
        item_id = hashlib.md5(
            f"{content}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        # Create item
        item = ClipboardItem(
            id=item_id,
            content=content,
            content_type=content_type,
            timestamp=datetime.now().isoformat()
        )

        # Add to history (at beginning)
        self.clipboard_history.insert(0, item)

        # Trim history if needed
        if len(self.clipboard_history) > self.max_history_size:
            # Remove oldest non-pinned items
            self.clipboard_history = [
                item for item in self.clipboard_history
                if item.pinned
            ] + [
                item for item in self.clipboard_history
                if not item.pinned
            ][:self.max_history_size]

        logger.debug(f"Added to clipboard history: {item.preview}")

    # =========================================================================
    # Import/Export
    # =========================================================================

    async def _export_history(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """Export clipboard history to file"""
        try:
            export_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "items": [asdict(item) for item in self.clipboard_history]
            }

            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            return {
                "success": True,
                "message": f"Exported {len(self.clipboard_history)} items",
                "file_path": str(path)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Export failed: {str(e)}"
            }

    async def _import_history(self, file_path: str, merge: bool = True, **kwargs) -> Dict[str, Any]:
        """Import clipboard history from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported_items = [
                ClipboardItem(**item_data)
                for item_data in data.get("items", [])
            ]

            if merge:
                # Merge with existing history
                existing_ids = {item.id for item in self.clipboard_history}
                new_items = [item for item in imported_items if item.id not in existing_ids]
                self.clipboard_history.extend(new_items)
                count = len(new_items)
            else:
                # Replace history
                self.clipboard_history = imported_items
                count = len(imported_items)

            await self._save_history()

            return {
                "success": True,
                "message": f"Imported {count} items",
                "total_items": len(self.clipboard_history)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Import failed: {str(e)}"
            }

    # =========================================================================
    # Statistics
    # =========================================================================

    async def _get_stats(self, **kwargs) -> Dict[str, Any]:
        """Get clipboard usage statistics"""
        if not self.clipboard_history:
            return {
                "total_items": 0,
                "pinned_items": 0,
                "monitoring_active": self.auto_capture
            }

        content_types = {}
        for item in self.clipboard_history:
            content_types[item.content_type] = content_types.get(item.content_type, 0) + 1

        return {
            "total_items": len(self.clipboard_history),
            "pinned_items": len(self.pinned_items),
            "content_types": content_types,
            "monitoring_active": self.auto_capture,
            "max_history_size": self.max_history_size,
            "oldest_item": self.clipboard_history[-1].timestamp if self.clipboard_history else None,
            "newest_item": self.clipboard_history[0].timestamp if self.clipboard_history else None
        }

    # =========================================================================
    # Persistence
    # =========================================================================

    async def _save_history(self):
        """Save clipboard history to disk"""
        try:
            history_file = Path.home() / ".windows_ai" / "clipboard_history.json"
            history_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "items": [asdict(item) for item in self.clipboard_history]
            }

            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved clipboard history: {len(self.clipboard_history)} items")

        except Exception as e:
            logger.error(f"Failed to save clipboard history: {e}")

    async def _load_history(self):
        """Load clipboard history from disk"""
        try:
            history_file = Path.home() / ".windows_ai" / "clipboard_history.json"

            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.clipboard_history = [
                    ClipboardItem(**item_data)
                    for item_data in data.get("items", [])
                ]

                # Rebuild pinned items list
                self.pinned_items = [item for item in self.clipboard_history if item.pinned]

                logger.info(f"Loaded clipboard history: {len(self.clipboard_history)} items")

        except Exception as e:
            logger.warning(f"Could not load clipboard history: {e}")


# Export
__all__ = ["WindowsClipboardManagerPlugin"]
