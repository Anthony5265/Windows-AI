"""
Working Memory Plugin
Short-term active information processing with attention and capacity limits
"""

from typing import Dict, Any, Optional, List
from collections import deque


class WorkingMemoryPlugin:
    """Plugin for working memory simulation"""

    name = "working_memory"
    version = "1.0.0"
    description = "Short-term memory with attention mechanisms and capacity limits"
    author = "Windows AI Team"

    def __init__(self):
        self.active_items = deque()
        self.attention_weights = {}
        self.capacity = 7  # Miller's Law: 7±2 items
        self.rehearsal_buffer = []
        self.encoding_strength = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Working Memory plugin"""
        try:
            if config:
                self.capacity = config.get("capacity", 7)
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Working Memory plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Working Memory action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "add_item":
                return self._add_item(params)
            elif action == "retrieve_item":
                return self._retrieve_item(params)
            elif action == "focus_attention":
                return self._focus_attention(params)
            elif action == "rehearse":
                return self._rehearse(params)
            elif action == "update_item":
                return self._update_item(params)
            elif action == "decay":
                return self._decay(params)
            elif action == "get_capacity_info":
                return self._get_capacity_info()
            elif action == "chunk_items":
                return self._chunk_items(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _add_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add an item to working memory"""
        item_id = params.get("item_id", f"item_{len(self.active_items)}")
        content = params.get("content", "")
        importance = params.get("importance", 0.5)
        item_type = params.get("type", "information")

        # Check capacity
        if len(self.active_items) >= self.capacity:
            # Evict least important item
            evicted = self._evict_item()
        else:
            evicted = None

        item = {
            "id": item_id,
            "content": content,
            "type": item_type,
            "importance": importance,
            "activation": 1.0,
            "rehearsal_count": 0,
            "added_at": "now"
        }

        self.active_items.append(item)
        self.attention_weights[item_id] = importance
        self.encoding_strength[item_id] = 0.5  # Initial encoding strength

        return {
            "success": True,
            "item": item,
            "evicted": evicted,
            "current_load": len(self.active_items),
            "capacity": self.capacity,
            "load_percentage": (len(self.active_items) / self.capacity) * 100
        }

    def _evict_item(self) -> Dict[str, Any]:
        """Evict least important item from working memory"""
        if not self.active_items:
            return None

        # Find item with lowest combined score (activation * importance)
        min_score = float('inf')
        min_idx = 0

        for i, item in enumerate(self.active_items):
            score = item["activation"] * item["importance"]
            if score < min_score:
                min_score = score
                min_idx = i

        evicted = self.active_items[min_idx]
        del self.active_items[min_idx]

        # Clean up associated data
        if evicted["id"] in self.attention_weights:
            del self.attention_weights[evicted["id"]]
        if evicted["id"] in self.encoding_strength:
            del self.encoding_strength[evicted["id"]]

        return evicted

    def _retrieve_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve an item from working memory"""
        item_id = params.get("item_id", "")
        query = params.get("query", "")

        if item_id:
            # Retrieve by ID
            for item in self.active_items:
                if item["id"] == item_id:
                    # Boost activation on retrieval
                    item["activation"] = min(item["activation"] + 0.1, 1.0)
                    return {
                        "success": True,
                        "item": item,
                        "retrieval_method": "direct"
                    }

            return {"success": False, "error": f"Item {item_id} not found in working memory"}

        elif query:
            # Retrieve by content match
            matches = []
            for item in self.active_items:
                if query.lower() in str(item["content"]).lower():
                    matches.append(item)
                    # Boost activation
                    item["activation"] = min(item["activation"] + 0.1, 1.0)

            if matches:
                # Return most activated match
                best_match = max(matches, key=lambda x: x["activation"])
                return {
                    "success": True,
                    "item": best_match,
                    "all_matches": len(matches),
                    "retrieval_method": "content_match"
                }

            return {"success": False, "error": "No matching items found"}

        return {"success": False, "error": "Must provide item_id or query"}

    def _focus_attention(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Focus attention on specific items"""
        item_ids = params.get("item_ids", [])
        attention_strength = params.get("strength", 1.0)

        if not item_ids:
            return {"success": False, "error": "No items specified"}

        focused_items = []

        for item in self.active_items:
            if item["id"] in item_ids:
                # Increase activation for focused items
                item["activation"] = min(item["activation"] + attention_strength * 0.2, 1.0)
                self.attention_weights[item["id"]] = min(
                    self.attention_weights.get(item["id"], 0.5) + attention_strength * 0.1,
                    1.0
                )
                focused_items.append(item)
            else:
                # Slight decay for non-focused items
                item["activation"] = max(item["activation"] - 0.05, 0.1)

        return {
            "success": True,
            "focused_items": focused_items,
            "num_focused": len(focused_items),
            "attention_distribution": self.attention_weights
        }

    def _rehearse(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Rehearse items to maintain or strengthen them"""
        item_ids = params.get("item_ids", [])
        rehearsal_type = params.get("type", "maintenance")  # maintenance or elaborative

        if not item_ids:
            # Rehearse all items
            item_ids = [item["id"] for item in self.active_items]

        rehearsed = []

        for item in self.active_items:
            if item["id"] in item_ids:
                item["rehearsal_count"] += 1

                if rehearsal_type == "maintenance":
                    # Simply maintain activation
                    item["activation"] = min(item["activation"] + 0.1, 1.0)
                    encoding_boost = 0.05

                elif rehearsal_type == "elaborative":
                    # Stronger effect, better encoding
                    item["activation"] = min(item["activation"] + 0.2, 1.0)
                    encoding_boost = 0.15

                # Improve encoding strength
                self.encoding_strength[item["id"]] = min(
                    self.encoding_strength.get(item["id"], 0.5) + encoding_boost,
                    1.0
                )

                rehearsed.append(item)

        return {
            "success": True,
            "rehearsed_items": rehearsed,
            "rehearsal_type": rehearsal_type,
            "num_rehearsed": len(rehearsed)
        }

    def _update_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update an item's content in working memory"""
        item_id = params.get("item_id", "")
        new_content = params.get("content")
        new_importance = params.get("importance")

        for item in self.active_items:
            if item["id"] == item_id:
                if new_content is not None:
                    item["content"] = new_content
                    # Reset activation as it's new information
                    item["activation"] = 0.8

                if new_importance is not None:
                    item["importance"] = new_importance
                    self.attention_weights[item_id] = new_importance

                return {
                    "success": True,
                    "updated_item": item
                }

        return {"success": False, "error": f"Item {item_id} not found"}

    def _decay(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Apply natural decay to all items in working memory"""
        decay_rate = params.get("decay_rate", 0.1)
        time_steps = params.get("time_steps", 1)

        decayed_items = []
        removed_items = []

        for _ in range(time_steps):
            items_to_remove = []

            for i, item in enumerate(self.active_items):
                # Decay activation
                item["activation"] -= decay_rate * (1.0 - item["importance"])
                item["activation"] = max(item["activation"], 0.0)

                # If activation drops too low, mark for removal
                if item["activation"] < 0.1:
                    items_to_remove.append(i)
                else:
                    decayed_items.append(item)

            # Remove items with very low activation
            for i in sorted(items_to_remove, reverse=True):
                removed = self.active_items[i]
                del self.active_items[i]
                removed_items.append(removed)

                # Clean up
                if removed["id"] in self.attention_weights:
                    del self.attention_weights[removed["id"]]
                if removed["id"] in self.encoding_strength:
                    del self.encoding_strength[removed["id"]]

        return {
            "success": True,
            "decay_rate": decay_rate,
            "time_steps": time_steps,
            "items_remaining": len(self.active_items),
            "items_decayed": len(decayed_items),
            "items_removed": len(removed_items),
            "removed_items": removed_items
        }

    def _get_capacity_info(self) -> Dict[str, Any]:
        """Get information about working memory capacity and load"""
        current_load = len(self.active_items)
        load_percentage = (current_load / self.capacity) * 100

        # Calculate average activation
        avg_activation = sum(item["activation"] for item in self.active_items) / current_load if current_load > 0 else 0

        # Get most and least active items
        if self.active_items:
            most_active = max(self.active_items, key=lambda x: x["activation"])
            least_active = min(self.active_items, key=lambda x: x["activation"])
        else:
            most_active = None
            least_active = None

        return {
            "success": True,
            "capacity": self.capacity,
            "current_load": current_load,
            "available_slots": self.capacity - current_load,
            "load_percentage": load_percentage,
            "average_activation": avg_activation,
            "most_active_item": most_active,
            "least_active_item": least_active,
            "total_rehearsals": sum(item["rehearsal_count"] for item in self.active_items)
        }

    def _chunk_items(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Chunk multiple items together to save capacity"""
        item_ids = params.get("item_ids", [])
        chunk_id = params.get("chunk_id", f"chunk_{len([i for i in self.active_items if i['type'] == 'chunk'])}")
        chunk_label = params.get("label", "")

        if len(item_ids) < 2:
            return {"success": False, "error": "Need at least 2 items to chunk"}

        # Find and remove items to be chunked
        items_to_chunk = []
        for item_id in item_ids:
            for item in self.active_items:
                if item["id"] == item_id:
                    items_to_chunk.append(item)
                    break

        if len(items_to_chunk) != len(item_ids):
            return {"success": False, "error": "Some items not found"}

        # Remove individual items
        for item in items_to_chunk:
            self.active_items.remove(item)
            if item["id"] in self.attention_weights:
                del self.attention_weights[item["id"]]
            if item["id"] in self.encoding_strength:
                del self.encoding_strength[item["id"]]

        # Create chunk
        chunk = {
            "id": chunk_id,
            "content": items_to_chunk,
            "type": "chunk",
            "label": chunk_label,
            "importance": max(item["importance"] for item in items_to_chunk),
            "activation": sum(item["activation"] for item in items_to_chunk) / len(items_to_chunk),
            "rehearsal_count": 0,
            "chunk_size": len(items_to_chunk),
            "added_at": "now"
        }

        self.active_items.append(chunk)
        self.attention_weights[chunk_id] = chunk["importance"]
        self.encoding_strength[chunk_id] = 0.7  # Chunks encode better

        return {
            "success": True,
            "chunk": chunk,
            "items_chunked": len(items_to_chunk),
            "capacity_saved": len(items_to_chunk) - 1,
            "new_load": len(self.active_items)
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.active_items = deque()
        self.attention_weights = {}
        self.rehearsal_buffer = []
        self.encoding_strength = {}
        return True
