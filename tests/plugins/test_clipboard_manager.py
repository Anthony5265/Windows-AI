"""
Tests for Windows Clipboard Manager Plugin
"""

import pytest
from unittest.mock import Mock, patch

from windows_ai.plugins.builtin.windows_clipboard_manager import WindowsClipboardManagerPlugin


class TestWindowsClipboardManagerPlugin:
    """Test suite for Clipboard Manager Plugin"""

    @pytest.fixture
    async def plugin(self):
        """Create plugin instance"""
        plugin = WindowsClipboardManagerPlugin()

        # Mock pyperclip
        plugin.pyperclip = Mock()
        plugin.pyperclip.paste = Mock(return_value="test content")
        plugin.pyperclip.copy = Mock()

        await plugin.initialize()
        yield plugin
        await plugin.shutdown()

    @pytest.mark.asyncio
    async def test_initialization(self, plugin):
        """Test plugin initialization"""
        assert plugin.metadata.id == "windows_clipboard_manager"
        assert plugin.max_history_size > 0

    @pytest.mark.asyncio
    async def test_get_current(self, plugin):
        """Test getting current clipboard content"""
        result = await plugin.execute("get_current", {})

        assert result["success"] is True
        assert "result" in result
        assert "content" in result["result"]

    @pytest.mark.asyncio
    async def test_set_clipboard(self, plugin):
        """Test setting clipboard content"""
        test_content = "Hello, World!"

        result = await plugin.execute("set_clipboard", {
            "content": test_content
        })

        assert result["success"] is True
        plugin.pyperclip.copy.assert_called_once_with(test_content)

    @pytest.mark.asyncio
    async def test_get_history(self, plugin):
        """Test getting clipboard history"""
        # Add some items to history
        await plugin.execute("set_clipboard", {"content": "Item 1"})
        await plugin.execute("set_clipboard", {"content": "Item 2"})
        await plugin.execute("set_clipboard", {"content": "Item 3"})

        result = await plugin.execute("get_history", {"limit": 10})

        assert result["success"] is True
        assert "result" in result
        assert "items" in result["result"]
        assert len(result["result"]["items"]) > 0

    @pytest.mark.asyncio
    async def test_search(self, plugin):
        """Test searching clipboard history"""
        # Add items
        await plugin.execute("set_clipboard", {"content": "Python code"})
        await plugin.execute("set_clipboard", {"content": "JavaScript code"})
        await plugin.execute("set_clipboard", {"content": "Random text"})

        result = await plugin.execute("search", {
            "search_query": "code"
        })

        assert result["success"] is True
        assert "result" in result
        assert "items" in result["result"]
        # Should find at least the items containing "code"
        assert len(result["result"]["items"]) >= 2

    @pytest.mark.asyncio
    async def test_pin_unpin(self, plugin):
        """Test pinning and unpinning items"""
        # Add item
        await plugin.execute("set_clipboard", {"content": "Important text"})

        # Get the item ID
        history = await plugin.execute("get_history", {"limit": 1})
        item_id = history["result"]["items"][0]["id"]

        # Pin the item
        result = await plugin.execute("pin", {"item_id": item_id})
        assert result["success"] is True

        # Check pinned items
        pinned = await plugin.execute("get_pinned", {})
        assert len(pinned["result"]["items"]) == 1

        # Unpin
        result = await plugin.execute("unpin", {"item_id": item_id})
        assert result["success"] is True

        # Check pinned items again
        pinned = await plugin.execute("get_pinned", {})
        assert len(pinned["result"]["items"]) == 0

    @pytest.mark.asyncio
    async def test_delete_item(self, plugin):
        """Test deleting clipboard item"""
        # Add item
        await plugin.execute("set_clipboard", {"content": "To be deleted"})

        # Get item ID
        history = await plugin.execute("get_history", {"limit": 1})
        initial_count = len(history["result"]["items"])
        item_id = history["result"]["items"][0]["id"]

        # Delete
        result = await plugin.execute("delete", {"item_id": item_id})
        assert result["success"] is True

        # Verify deletion
        history = await plugin.execute("get_history", {"limit": 10})
        assert len(history["result"]["items"]) < initial_count

    @pytest.mark.asyncio
    async def test_clear_history(self, plugin):
        """Test clearing history"""
        # Add items
        for i in range(5):
            await plugin.execute("set_clipboard", {"content": f"Item {i}"})

        # Clear history
        result = await plugin.execute("clear_history", {"keep_pinned": False})
        assert result["success"] is True

        # Verify cleared
        history = await plugin.execute("get_history", {"limit": 10})
        assert len(history["result"]["items"]) == 0

    @pytest.mark.asyncio
    async def test_clear_history_keep_pinned(self, plugin):
        """Test clearing history but keeping pinned items"""
        # Add items
        await plugin.execute("set_clipboard", {"content": "Regular item"})
        await plugin.execute("set_clipboard", {"content": "Pinned item"})

        # Pin one item
        history = await plugin.execute("get_history", {"limit": 10})
        pinned_id = history["result"]["items"][0]["id"]
        await plugin.execute("pin", {"item_id": pinned_id})

        # Clear keeping pinned
        result = await plugin.execute("clear_history", {"keep_pinned": True})
        assert result["success"] is True

        # Verify pinned item remains
        history = await plugin.execute("get_history", {"limit": 10})
        assert len(history["result"]["items"]) == 1

    @pytest.mark.asyncio
    async def test_get_stats(self, plugin):
        """Test getting statistics"""
        # Add some items
        for i in range(3):
            await plugin.execute("set_clipboard", {"content": f"Item {i}"})

        result = await plugin.execute("get_stats", {})

        assert result["success"] is True
        assert "result" in result
        assert "total_items" in result["result"]
        assert result["result"]["total_items"] >= 3

    @pytest.mark.asyncio
    async def test_export_import(self, plugin, tmp_path):
        """Test export and import functionality"""
        # Add items
        await plugin.execute("set_clipboard", {"content": "Export test 1"})
        await plugin.execute("set_clipboard", {"content": "Export test 2"})

        # Export
        export_path = tmp_path / "clipboard_export.json"
        result = await plugin.execute("export", {
            "file_path": str(export_path)
        })

        assert result["success"] is True
        assert export_path.exists()

        # Clear history
        await plugin.execute("clear_history", {"keep_pinned": False})

        # Import
        result = await plugin.execute("import", {
            "file_path": str(export_path),
            "merge": False
        })

        assert result["success"] is True

        # Verify imported
        history = await plugin.execute("get_history", {"limit": 10})
        assert len(history["result"]["items"]) > 0

    def test_get_schema(self, plugin):
        """Test schema generation"""
        schema = plugin.get_schema()

        assert "properties" in schema
        assert "action" in schema["properties"]
        assert "required" in schema
