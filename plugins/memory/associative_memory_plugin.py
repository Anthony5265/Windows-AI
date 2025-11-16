"""
Associative Memory Plugin
Link concepts and memories through associations with spreading activation
"""

from typing import Dict, Any, Optional, List, Set
from collections import defaultdict, deque


class AssociativeMemoryPlugin:
    """Plugin for associative memory with spreading activation"""

    name = "associative_memory"
    version = "1.0.0"
    description = "Link concepts through associations with spreading activation"
    author = "Windows AI Team"

    def __init__(self):
        self.concepts = {}
        self.associations = defaultdict(list)  # concept_id -> [(related_id, strength), ...]
        self.activation_levels = {}
        self.priming_effects = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Associative Memory plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Associative Memory plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute an Associative Memory action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "add_concept":
                return self._add_concept(params)
            elif action == "create_association":
                return self._create_association(params)
            elif action == "activate":
                return self._activate(params)
            elif action == "spread_activation":
                return self._spread_activation(params)
            elif action == "prime":
                return self._prime(params)
            elif action == "recall_by_association":
                return self._recall_by_association(params)
            elif action == "get_related":
                return self._get_related(params)
            elif action == "strengthen_association":
                return self._strengthen_association(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _add_concept(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a concept to associative memory"""
        concept_id = params.get("concept_id", f"concept_{len(self.concepts)}")
        content = params.get("content", "")
        concept_type = params.get("type", "general")
        metadata = params.get("metadata", {})

        concept = {
            "id": concept_id,
            "content": content,
            "type": concept_type,
            "metadata": metadata,
            "access_count": 0,
            "created_at": "now"
        }

        self.concepts[concept_id] = concept
        self.activation_levels[concept_id] = 0.0

        return {
            "success": True,
            "concept": concept,
            "total_concepts": len(self.concepts)
        }

    def _create_association(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create an association between two concepts"""
        source_id = params.get("source_id", "")
        target_id = params.get("target_id", "")
        strength = params.get("strength", 0.5)
        association_type = params.get("type", "related")
        bidirectional = params.get("bidirectional", True)

        # Validate concepts exist
        if source_id not in self.concepts:
            return {"success": False, "error": f"Source concept {source_id} not found"}
        if target_id not in self.concepts:
            return {"success": False, "error": f"Target concept {target_id} not found"}

        # Create association
        association = {
            "target_id": target_id,
            "strength": strength,
            "type": association_type,
            "created_at": "now",
            "activation_count": 0
        }

        # Check if association already exists
        existing = None
        for assoc in self.associations[source_id]:
            if assoc["target_id"] == target_id:
                existing = assoc
                break

        if existing:
            # Update existing association
            existing["strength"] = min(existing["strength"] + strength * 0.1, 1.0)
            existing["activation_count"] += 1
        else:
            # Add new association
            self.associations[source_id].append(association)

        # Create reverse association if bidirectional
        if bidirectional:
            reverse_association = {
                "target_id": source_id,
                "strength": strength,
                "type": association_type,
                "created_at": "now",
                "activation_count": 0
            }

            existing_reverse = None
            for assoc in self.associations[target_id]:
                if assoc["target_id"] == source_id:
                    existing_reverse = assoc
                    break

            if existing_reverse:
                existing_reverse["strength"] = min(existing_reverse["strength"] + strength * 0.1, 1.0)
            else:
                self.associations[target_id].append(reverse_association)

        return {
            "success": True,
            "source_id": source_id,
            "target_id": target_id,
            "strength": strength,
            "bidirectional": bidirectional,
            "source_associations": len(self.associations[source_id]),
            "target_associations": len(self.associations[target_id])
        }

    def _activate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Activate a concept"""
        concept_id = params.get("concept_id", "")
        activation_strength = params.get("strength", 1.0)

        if concept_id not in self.concepts:
            return {"success": False, "error": f"Concept {concept_id} not found"}

        # Set activation level
        self.activation_levels[concept_id] = min(
            self.activation_levels.get(concept_id, 0.0) + activation_strength,
            1.0
        )

        # Update access count
        self.concepts[concept_id]["access_count"] += 1

        return {
            "success": True,
            "concept_id": concept_id,
            "activation_level": self.activation_levels[concept_id],
            "access_count": self.concepts[concept_id]["access_count"]
        }

    def _spread_activation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Spread activation from a concept to related concepts"""
        source_id = params.get("source_id", "")
        max_depth = params.get("max_depth", 2)
        decay_rate = params.get("decay_rate", 0.5)
        threshold = params.get("threshold", 0.1)

        if source_id not in self.concepts:
            return {"success": False, "error": f"Source concept {source_id} not found"}

        # Initialize spreading activation
        activated = {}
        queue = deque([(source_id, 1.0, 0)])  # (concept_id, activation, depth)
        visited = set()

        while queue:
            current_id, current_activation, depth = queue.popleft()

            if current_id in visited or depth > max_depth:
                continue

            visited.add(current_id)
            activated[current_id] = current_activation

            # Update activation level
            self.activation_levels[current_id] = min(
                self.activation_levels.get(current_id, 0.0) + current_activation,
                1.0
            )

            # Spread to related concepts
            if depth < max_depth:
                for assoc in self.associations[current_id]:
                    target_id = assoc["target_id"]
                    assoc_strength = assoc["strength"]

                    # Calculate spread activation
                    spread_strength = current_activation * assoc_strength * decay_rate

                    if spread_strength >= threshold and target_id not in visited:
                        queue.append((target_id, spread_strength, depth + 1))
                        assoc["activation_count"] += 1

        # Get activated concepts with their details
        activated_concepts = []
        for concept_id, activation in sorted(activated.items(), key=lambda x: x[1], reverse=True):
            if concept_id != source_id:  # Exclude source
                activated_concepts.append({
                    "concept_id": concept_id,
                    "content": self.concepts[concept_id]["content"],
                    "activation": activation,
                    "current_level": self.activation_levels[concept_id]
                })

        return {
            "success": True,
            "source_id": source_id,
            "activated_concepts": activated_concepts,
            "num_activated": len(activated_concepts),
            "max_depth_reached": depth,
            "activation_map": activated
        }

    def _prime(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prime concepts to make them more accessible"""
        concept_ids = params.get("concept_ids", [])
        priming_strength = params.get("strength", 0.3)
        duration = params.get("duration", "temporary")  # temporary or persistent

        primed = []

        for concept_id in concept_ids:
            if concept_id not in self.concepts:
                continue

            # Apply priming
            self.priming_effects[concept_id] = {
                "strength": priming_strength,
                "duration": duration,
                "applied_at": "now"
            }

            # Boost activation
            self.activation_levels[concept_id] = min(
                self.activation_levels.get(concept_id, 0.0) + priming_strength,
                1.0
            )

            primed.append({
                "concept_id": concept_id,
                "content": self.concepts[concept_id]["content"],
                "priming_strength": priming_strength,
                "new_activation": self.activation_levels[concept_id]
            })

        return {
            "success": True,
            "primed_concepts": primed,
            "num_primed": len(primed),
            "duration": duration
        }

    def _recall_by_association(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recall concepts based on associative cues"""
        cue_ids = params.get("cue_ids", [])
        min_strength = params.get("min_strength", 0.3)
        max_results = params.get("max_results", 10)

        if not cue_ids:
            return {"success": False, "error": "No cue concepts provided"}

        # Collect all associated concepts
        recalled = {}

        for cue_id in cue_ids:
            if cue_id not in self.concepts:
                continue

            # Get direct associations
            for assoc in self.associations[cue_id]:
                target_id = assoc["target_id"]
                strength = assoc["strength"]

                if strength >= min_strength:
                    if target_id in recalled:
                        # Strengthen if multiple cues point to same concept
                        recalled[target_id] = min(recalled[target_id] + strength * 0.5, 1.0)
                    else:
                        recalled[target_id] = strength

        # Sort by strength and get top results
        sorted_recalled = sorted(recalled.items(), key=lambda x: x[1], reverse=True)[:max_results]

        recalled_concepts = []
        for concept_id, strength in sorted_recalled:
            recalled_concepts.append({
                "concept_id": concept_id,
                "content": self.concepts[concept_id]["content"],
                "type": self.concepts[concept_id]["type"],
                "association_strength": strength,
                "activation_level": self.activation_levels.get(concept_id, 0.0),
                "is_primed": concept_id in self.priming_effects
            })

        return {
            "success": True,
            "cues": cue_ids,
            "recalled_concepts": recalled_concepts,
            "num_recalled": len(recalled_concepts)
        }

    def _get_related(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get concepts related to a given concept"""
        concept_id = params.get("concept_id", "")
        min_strength = params.get("min_strength", 0.0)
        association_type = params.get("type", None)

        if concept_id not in self.concepts:
            return {"success": False, "error": f"Concept {concept_id} not found"}

        related = []

        for assoc in self.associations[concept_id]:
            # Filter by type if specified
            if association_type and assoc["type"] != association_type:
                continue

            # Filter by strength
            if assoc["strength"] < min_strength:
                continue

            target_id = assoc["target_id"]
            related.append({
                "concept_id": target_id,
                "content": self.concepts[target_id]["content"],
                "association_strength": assoc["strength"],
                "association_type": assoc["type"],
                "activation_count": assoc["activation_count"]
            })

        # Sort by strength
        related.sort(key=lambda x: x["association_strength"], reverse=True)

        return {
            "success": True,
            "concept_id": concept_id,
            "related_concepts": related,
            "num_related": len(related)
        }

    def _strengthen_association(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Strengthen an existing association through repeated activation"""
        source_id = params.get("source_id", "")
        target_id = params.get("target_id", "")
        boost = params.get("boost", 0.1)

        if source_id not in self.concepts:
            return {"success": False, "error": f"Source concept {source_id} not found"}
        if target_id not in self.concepts:
            return {"success": False, "error": f"Target concept {target_id} not found"}

        # Find and strengthen association
        strengthened = False
        old_strength = 0.0
        new_strength = 0.0

        for assoc in self.associations[source_id]:
            if assoc["target_id"] == target_id:
                old_strength = assoc["strength"]
                assoc["strength"] = min(assoc["strength"] + boost, 1.0)
                new_strength = assoc["strength"]
                assoc["activation_count"] += 1
                strengthened = True
                break

        if not strengthened:
            return {"success": False, "error": "Association not found"}

        return {
            "success": True,
            "source_id": source_id,
            "target_id": target_id,
            "old_strength": old_strength,
            "new_strength": new_strength,
            "boost_applied": boost
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.concepts = {}
        self.associations = defaultdict(list)
        self.activation_levels = {}
        self.priming_effects = {}
        return True
