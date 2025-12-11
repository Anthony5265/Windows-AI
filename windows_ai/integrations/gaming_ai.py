"""
Gaming & Entertainment AI Manager - 15+ Services
Game AI, NPC behavior, procedural generation, game analytics
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
import random

logger = logging.getLogger(__name__)

class GamingAIManager:
    """Unified gaming AI across 15+ services"""

    def __init__(self):
        self._config: Optional[WindowsAIConfig] = None
        self._initialized = False

    async def initialize(self, config: Optional[WindowsAIConfig] = None):
        if self._initialized:
            return
        
        self._config = config
        self._initialized = True

    # ==================== NPC DIALOGUE ====================

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

    async def generate_npc_dialogue(self, npc_profile: Dict, context: str, player_input: str) -> Dict:
        """Generate contextual NPC dialogue"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""You are an NPC in a game. Stay in character.
Character: {npc_profile.get('name', 'Unknown')}
Personality: {npc_profile.get('personality', 'neutral')}
Role: {npc_profile.get('role', 'villager')}
Background: {npc_profile.get('backstory', 'A simple inhabitant')}
Current mood: {npc_profile.get('mood', 'neutral')}

Respond naturally, staying in character. Include actions in *asterisks*.
Context: {context}"""},
            {"role": "user", "content": player_input}
        ]

        response = await ai.chat(Provider.OPENAI, messages, temperature=0.8)
        return {"npc": npc_profile.get("name"), "dialogue": response["content"]}

    async def generate_quest(self, theme: str, difficulty: str = "medium", player_level: int = 1) -> Dict:
        """Generate dynamic quest"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""Generate a game quest with:
Theme: {theme}
Difficulty: {difficulty}
Player Level: {player_level}

Include:
1. Quest name
2. Description
3. Objectives (list)
4. NPCs involved
5. Locations
6. Rewards
7. Optional bonus objectives
Return JSON."""},
            {"role": "user", "content": f"Create an engaging {theme} quest"}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"quest": response["content"]}

    # ==================== PROCEDURAL GENERATION ====================

    async def generate_world(self, world_type: str, size: str = "medium", seed: int = None) -> Dict:
        """Generate procedural world"""
        import numpy as np

        seed = seed or random.randint(0, 999999)
        np.random.seed(seed)

        sizes = {"small": 50, "medium": 100, "large": 200}
        world_size = sizes.get(size, 100)

        # Generate heightmap using noise
        heightmap = self._generate_noise(world_size, world_size)

        # Generate biomes based on height
        biomes = self._assign_biomes(heightmap, world_type)

        # Generate points of interest
        pois = self._generate_pois(world_size, world_type)

        return {
            "seed": seed,
            "size": world_size,
            "type": world_type,
            "heightmap_shape": heightmap.shape,
            "biomes": list(set(biomes.flatten().tolist())),
            "points_of_interest": pois
        }

    def _generate_noise(self, width: int, height: int) -> Any:
        import numpy as np
        # Simplified perlin-like noise
        noise = np.zeros((height, width))
        for i in range(5):
            scale = 2 ** i
            noise += np.random.rand(height // scale + 1, width // scale + 1).repeat(scale, axis=0).repeat(scale, axis=1)[:height, :width] / scale
        return noise / noise.max()

    def _assign_biomes(self, heightmap, world_type) -> Any:
        import numpy as np
        biomes = np.empty(heightmap.shape, dtype=object)
        biomes[heightmap < 0.3] = "water"
        biomes[(heightmap >= 0.3) & (heightmap < 0.5)] = "plains"
        biomes[(heightmap >= 0.5) & (heightmap < 0.7)] = "forest"
        biomes[(heightmap >= 0.7) & (heightmap < 0.85)] = "hills"
        biomes[heightmap >= 0.85] = "mountains"
        return biomes

    def _generate_pois(self, world_size: int, world_type: str) -> List[Dict]:
        poi_types = {
            "fantasy": ["castle", "dungeon", "village", "ruins", "tower", "shrine"],
            "scifi": ["outpost", "station", "wreckage", "colony", "facility"],
            "modern": ["city", "town", "military_base", "airport", "port"]
        }
        types = poi_types.get(world_type, poi_types["fantasy"])
        num_pois = world_size // 10
        return [{"type": random.choice(types), "x": random.randint(0, world_size), "y": random.randint(0, world_size)}
                for _ in range(num_pois)]

    async def generate_dungeon(self, theme: str, rooms: int = 10, difficulty: str = "medium") -> Dict:
        """Generate procedural dungeon"""
        room_types = ["entrance", "corridor", "treasure_room", "trap_room", "monster_lair", "puzzle_room", "boss_room"]
        enemy_types = {"easy": ["goblin", "rat", "skeleton"], "medium": ["orc", "zombie", "ghost"], "hard": ["dragon", "demon", "lich"]}

        dungeon_rooms = []
        for i in range(rooms):
            room_type = "entrance" if i == 0 else "boss_room" if i == rooms - 1 else random.choice(room_types[1:-1])
            dungeon_rooms.append({
                "id": i,
                "type": room_type,
                "connections": [i - 1] if i > 0 else [],
                "enemies": random.sample(enemy_types.get(difficulty, enemy_types["medium"]), random.randint(0, 3)) if room_type in ["monster_lair", "boss_room"] else [],
                "loot": random.randint(0, 100) if room_type == "treasure_room" else 0
            })

        return {"theme": theme, "difficulty": difficulty, "rooms": dungeon_rooms}

    async def generate_item(self, item_type: str, rarity: str = "common", level: int = 1) -> Dict:
        """Generate procedural item"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""Generate a game item:
Type: {item_type}
Rarity: {rarity}
Level: {level}

Include:
1. Name (creative, thematic)
2. Description
3. Stats/bonuses
4. Special abilities (if rare+)
5. Lore/history
Return JSON."""},
            {"role": "user", "content": f"Create a {rarity} {item_type}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"item": response["content"]}

    # ==================== GAME AI BEHAVIOR ====================

    async def calculate_ai_move(self, game_state: Dict, ai_player: str, strategy: str = "balanced") -> Dict:
        """Calculate AI player's next move"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""You are a game AI playing as {ai_player}.
Strategy: {strategy}
Analyze the game state and determine the optimal move.
Consider: position, resources, opponent moves, win conditions.
Return JSON: {{"move": "...", "reasoning": "...", "confidence": 0-100}}"""},
            {"role": "user", "content": f"Game state: {game_state}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"move": response["content"]}

    async def pathfinding(self, grid: List[List[int]], start: tuple, end: tuple) -> Dict:
        """A* pathfinding algorithm"""
        import heapq

        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

        rows, cols = len(grid), len(grid[0])
        open_set = [(0, start)]
        came_from = {}
        g_score = {start: 0}
        f_score = {start: heuristic(start, end)}

        while open_set:
            current = heapq.heappop(open_set)[1]

            if current == end:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return {"path": path[::-1], "length": len(path)}

            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)
                if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols and grid[neighbor[0]][neighbor[1]] == 0:
                    tentative_g = g_score[current] + 1
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score[neighbor] = tentative_g + heuristic(neighbor, end)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return {"path": [], "error": "No path found"}

    # ==================== GAME ANALYTICS ====================

    async def analyze_player_behavior(self, player_data: Dict) -> Dict:
        """Analyze player behavior patterns"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Analyze player behavior data:
1. Playstyle classification
2. Skill level assessment
3. Engagement patterns
4. Churn risk
5. Monetization potential
6. Personalization recommendations
Return JSON analysis."""},
            {"role": "user", "content": str(player_data)}
        ]

        response = await ai.chat(Provider.OPENAI, messages)
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"analysis": response["content"]}

    async def balance_game(self, game_data: Dict) -> Dict:
        """AI-powered game balancing suggestions"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": """Analyze game balance data and suggest:
1. Overpowered elements to nerf
2. Underpowered elements to buff
3. Economy balance adjustments
4. Difficulty curve optimization
5. Meta diversity improvements
Return specific, actionable recommendations."""},
            {"role": "user", "content": str(game_data)}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        return {"balancing": response["content"]}

    # ==================== NARRATIVE GENERATION ====================

    async def generate_story(self, genre: str, characters: List[Dict], setting: str) -> Dict:
        """Generate game narrative"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""Create a game narrative:
Genre: {genre}
Setting: {setting}

Include:
1. Main plot with acts
2. Character arcs
3. Key plot points
4. Multiple endings
5. Side story opportunities
Return structured JSON."""},
            {"role": "user", "content": f"Characters: {characters}"}
        ]

        response = await ai.chat(Provider.OPENAI, messages, model="gpt-4o")
        import json
        try:
            return json.loads(response["content"])
        except:
            return {"narrative": response["content"]}

    def list_capabilities(self) -> Dict[str, List[str]]:
        return {
            "dialogue": ["npc_conversation", "quest_dialogue", "branching_dialogue"],
            "procedural": ["world_generation", "dungeon_generation", "item_generation"],
            "ai_behavior": ["pathfinding", "decision_making", "difficulty_scaling"],
            "analytics": ["player_behavior", "game_balance", "engagement"],
            "narrative": ["story_generation", "quest_creation", "lore_building"]
        }
