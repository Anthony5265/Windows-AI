"""
Memory Consolidation Plugin
Simulate memory consolidation process - strengthening, merging, and organizing memories
"""

from typing import Dict, Any, Optional, List
import random


class MemoryConsolidationPlugin:
    """Plugin for memory consolidation and strengthening"""

    name = "memory_consolidation"
    version = "1.0.0"
    description = "Consolidate, strengthen, and organize memories over time"
    author = "Windows AI Team"

    def __init__(self):
        self.memories = {}
        self.consolidated_memories = {}
        self.consolidation_history = []
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Memory Consolidation plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Memory Consolidation plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Memory Consolidation action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "add_memory":
                return self._add_memory(params)
            elif action == "consolidate":
                return self._consolidate(params)
            elif action == "strengthen":
                return self._strengthen(params)
            elif action == "merge_similar":
                return self._merge_similar(params)
            elif action == "forget_weak":
                return self._forget_weak(params)
            elif action == "replay":
                return self._replay(params)
            elif action == "get_stability":
                return self._get_stability(params)
            elif action == "transfer_to_longterm":
                return self._transfer_to_longterm(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _add_memory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new memory"""
        memory_id = params.get("memory_id", f"mem_{len(self.memories)}")
        content = params.get("content", "")
        memory_type = params.get("type", "general")
        importance = params.get("importance", 0.5)
        emotional_valence = params.get("emotional_valence", 0.0)  # -1 to 1

        memory = {
            "id": memory_id,
            "content": content,
            "type": memory_type,
            "importance": importance,
            "emotional_valence": emotional_valence,
            "strength": 0.5,  # Initial encoding strength
            "stability": 0.3,  # How resistant to forgetting
            "rehearsal_count": 0,
            "consolidation_level": 0,  # 0=new, 1=partially, 2=well, 3=fully
            "created_at": "now",
            "last_accessed": "now",
            "related_memories": []
        }

        self.memories[memory_id] = memory

        return {
            "success": True,
            "memory": memory,
            "total_memories": len(self.memories)
        }

    def _consolidate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform consolidation process (like sleep)"""
        memory_ids = params.get("memory_ids", None)
        consolidation_strength = params.get("strength", 0.3)
        process_type = params.get("type", "full")  # full, selective, fast

        # If no specific memories, consolidate all recent ones
        if memory_ids is None:
            memories_to_consolidate = list(self.memories.values())
        else:
            memories_to_consolidate = [self.memories[mid] for mid in memory_ids if mid in self.memories]

        consolidated = []
        strengthened = []
        connected = []

        for memory in memories_to_consolidate:
            # Strengthen based on importance and emotional valence
            strength_boost = consolidation_strength * (
                0.5 + memory["importance"] * 0.3 + abs(memory["emotional_valence"]) * 0.2
            )

            memory["strength"] = min(memory["strength"] + strength_boost, 1.0)
            memory["stability"] = min(memory["stability"] + consolidation_strength * 0.2, 1.0)
            memory["consolidation_level"] = min(memory["consolidation_level"] + 1, 3)

            strengthened.append(memory["id"])

            # Find and strengthen connections to related memories
            for other_id, other_memory in self.memories.items():
                if other_id == memory["id"]:
                    continue

                # Calculate similarity (simplified)
                similarity = self._calculate_similarity(memory, other_memory)

                if similarity > 0.5:
                    if other_id not in memory["related_memories"]:
                        memory["related_memories"].append(other_id)
                    if memory["id"] not in other_memory["related_memories"]:
                        other_memory["related_memories"].append(memory["id"])
                    connected.append((memory["id"], other_id))

            consolidated.append({
                "memory_id": memory["id"],
                "new_strength": memory["strength"],
                "new_stability": memory["stability"],
                "consolidation_level": memory["consolidation_level"]
            })

        # Record consolidation event
        consolidation_event = {
            "type": process_type,
            "memories_processed": len(consolidated),
            "memories_strengthened": len(strengthened),
            "connections_made": len(connected),
            "timestamp": "now"
        }

        self.consolidation_history.append(consolidation_event)

        return {
            "success": True,
            "consolidated": consolidated,
            "num_processed": len(consolidated),
            "connections_made": len(connected),
            "consolidation_event": consolidation_event
        }

    def _calculate_similarity(self, mem1: Dict[str, Any], mem2: Dict[str, Any]) -> float:
        """Calculate similarity between two memories"""
        similarity = 0.0

        # Type similarity
        if mem1["type"] == mem2["type"]:
            similarity += 0.3

        # Emotional valence similarity
        valence_diff = abs(mem1["emotional_valence"] - mem2["emotional_valence"])
        similarity += (1.0 - valence_diff) * 0.2

        # Content similarity (simplified - would use embeddings in real implementation)
        content1 = set(str(mem1["content"]).lower().split())
        content2 = set(str(mem2["content"]).lower().split())

        if content1 and content2:
            overlap = len(content1 & content2) / len(content1 | content2)
            similarity += overlap * 0.5

        return min(similarity, 1.0)

    def _strengthen(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Strengthen specific memories through rehearsal"""
        memory_ids = params.get("memory_ids", [])
        strength_boost = params.get("boost", 0.1)

        strengthened = []

        for memory_id in memory_ids:
            if memory_id not in self.memories:
                continue

            memory = self.memories[memory_id]

            # Strengthen
            memory["strength"] = min(memory["strength"] + strength_boost, 1.0)
            memory["stability"] = min(memory["stability"] + strength_boost * 0.5, 1.0)
            memory["rehearsal_count"] += 1
            memory["last_accessed"] = "now"

            strengthened.append({
                "memory_id": memory_id,
                "new_strength": memory["strength"],
                "new_stability": memory["stability"],
                "rehearsal_count": memory["rehearsal_count"]
            })

        return {
            "success": True,
            "strengthened": strengthened,
            "num_strengthened": len(strengthened)
        }

    def _merge_similar(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Merge similar memories into consolidated memories"""
        similarity_threshold = params.get("threshold", 0.7)
        preserve_originals = params.get("preserve_originals", False)

        merged_groups = []
        processed = set()

        for mem1_id, mem1 in self.memories.items():
            if mem1_id in processed:
                continue

            similar_group = [mem1_id]

            # Find similar memories
            for mem2_id, mem2 in self.memories.items():
                if mem2_id == mem1_id or mem2_id in processed:
                    continue

                similarity = self._calculate_similarity(mem1, mem2)

                if similarity >= similarity_threshold:
                    similar_group.append(mem2_id)
                    processed.add(mem2_id)

            if len(similar_group) > 1:
                # Create merged memory
                merged_id = f"merged_{len(self.consolidated_memories)}"
                merged_memory = self._create_merged_memory(similar_group, merged_id)

                self.consolidated_memories[merged_id] = merged_memory
                merged_groups.append({
                    "merged_id": merged_id,
                    "source_memories": similar_group,
                    "merged_memory": merged_memory
                })

                # Optionally remove originals
                if not preserve_originals:
                    for mem_id in similar_group:
                        if mem_id in self.memories:
                            del self.memories[mem_id]

            processed.add(mem1_id)

        return {
            "success": True,
            "merged_groups": merged_groups,
            "num_groups": len(merged_groups),
            "preserved_originals": preserve_originals
        }

    def _create_merged_memory(self, memory_ids: List[str], merged_id: str) -> Dict[str, Any]:
        """Create a merged memory from multiple memories"""
        source_memories = [self.memories[mid] for mid in memory_ids if mid in self.memories]

        if not source_memories:
            return {}

        # Aggregate properties
        avg_importance = sum(m["importance"] for m in source_memories) / len(source_memories)
        avg_emotional_valence = sum(m["emotional_valence"] for m in source_memories) / len(source_memories)
        max_strength = max(m["strength"] for m in source_memories)
        max_stability = max(m["stability"] for m in source_memories)

        # Combine content
        combined_content = " | ".join([str(m["content"]) for m in source_memories])

        merged = {
            "id": merged_id,
            "content": combined_content,
            "type": "consolidated",
            "importance": avg_importance,
            "emotional_valence": avg_emotional_valence,
            "strength": max_strength,
            "stability": max_stability,
            "consolidation_level": 3,  # Fully consolidated
            "source_memories": memory_ids,
            "num_sources": len(source_memories),
            "created_at": "now"
        }

        return merged

    def _forget_weak(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove memories with low strength/stability (forgetting)"""
        strength_threshold = params.get("strength_threshold", 0.2)
        stability_threshold = params.get("stability_threshold", 0.1)

        forgotten = []
        retained = []

        for memory_id, memory in list(self.memories.items()):
            if memory["strength"] < strength_threshold and memory["stability"] < stability_threshold:
                # Forget this memory
                forgotten.append({
                    "memory_id": memory_id,
                    "strength": memory["strength"],
                    "stability": memory["stability"]
                })
                del self.memories[memory_id]
            else:
                retained.append(memory_id)

        return {
            "success": True,
            "forgotten": forgotten,
            "num_forgotten": len(forgotten),
            "num_retained": len(retained),
            "total_remaining": len(self.memories)
        }

    def _replay(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Replay memories to strengthen them (like memory replay during sleep)"""
        num_replays = params.get("num_replays", 5)
        selection_bias = params.get("bias", "importance")  # importance, recent, emotional, random

        replayed = []

        # Select memories to replay
        memory_list = list(self.memories.values())

        if not memory_list:
            return {"success": True, "replayed": [], "num_replayed": 0}

        for _ in range(min(num_replays, len(memory_list))):
            if selection_bias == "importance":
                # Bias toward important memories
                weights = [m["importance"] for m in memory_list]
            elif selection_bias == "emotional":
                # Bias toward emotional memories
                weights = [abs(m["emotional_valence"]) for m in memory_list]
            elif selection_bias == "recent":
                # Bias toward recent (simulated)
                weights = [1.0 / (i + 1) for i in range(len(memory_list))]
            else:
                # Random
                weights = [1.0] * len(memory_list)

            # Normalize weights
            total_weight = sum(weights)
            if total_weight > 0:
                weights = [w / total_weight for w in weights]
                memory = random.choices(memory_list, weights=weights, k=1)[0]
            else:
                memory = random.choice(memory_list)

            # Strengthen through replay
            memory["strength"] = min(memory["strength"] + 0.05, 1.0)
            memory["stability"] = min(memory["stability"] + 0.03, 1.0)
            memory["rehearsal_count"] += 1

            replayed.append({
                "memory_id": memory["id"],
                "content_preview": str(memory["content"])[:50] + "...",
                "new_strength": memory["strength"],
                "new_stability": memory["stability"]
            })

        return {
            "success": True,
            "replayed": replayed,
            "num_replayed": len(replayed),
            "selection_bias": selection_bias
        }

    def _get_stability(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get stability information for memories"""
        memory_id = params.get("memory_id", None)

        if memory_id:
            # Get specific memory
            if memory_id not in self.memories:
                return {"success": False, "error": f"Memory {memory_id} not found"}

            memory = self.memories[memory_id]
            return {
                "success": True,
                "memory_id": memory_id,
                "strength": memory["strength"],
                "stability": memory["stability"],
                "consolidation_level": memory["consolidation_level"],
                "rehearsal_count": memory["rehearsal_count"]
            }
        else:
            # Get overall statistics
            if not self.memories:
                return {"success": True, "statistics": {"total_memories": 0}}

            avg_strength = sum(m["strength"] for m in self.memories.values()) / len(self.memories)
            avg_stability = sum(m["stability"] for m in self.memories.values()) / len(self.memories)

            consolidation_levels = {0: 0, 1: 0, 2: 0, 3: 0}
            for memory in self.memories.values():
                consolidation_levels[memory["consolidation_level"]] += 1

            return {
                "success": True,
                "statistics": {
                    "total_memories": len(self.memories),
                    "average_strength": avg_strength,
                    "average_stability": avg_stability,
                    "consolidation_distribution": consolidation_levels,
                    "total_consolidated": len(self.consolidated_memories),
                    "consolidation_events": len(self.consolidation_history)
                }
            }

    def _transfer_to_longterm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transfer well-consolidated memories to long-term storage"""
        min_strength = params.get("min_strength", 0.7)
        min_stability = params.get("min_stability", 0.6)
        min_consolidation = params.get("min_consolidation_level", 2)

        transferred = []

        for memory_id, memory in list(self.memories.items()):
            if (memory["strength"] >= min_strength and
                memory["stability"] >= min_stability and
                memory["consolidation_level"] >= min_consolidation):

                # Transfer to long-term
                self.consolidated_memories[memory_id] = memory
                transferred.append({
                    "memory_id": memory_id,
                    "strength": memory["strength"],
                    "stability": memory["stability"],
                    "consolidation_level": memory["consolidation_level"]
                })

                # Remove from short-term
                del self.memories[memory_id]

        return {
            "success": True,
            "transferred": transferred,
            "num_transferred": len(transferred),
            "total_longterm": len(self.consolidated_memories),
            "total_shortterm": len(self.memories)
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.memories = {}
        self.consolidated_memories = {}
        self.consolidation_history = []
        return True
