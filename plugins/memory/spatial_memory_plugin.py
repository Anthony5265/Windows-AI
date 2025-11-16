"""
Spatial Memory Plugin
Store and retrieve spatial and location-based information
"""

from typing import Dict, Any, Optional, List
import math


class SpatialMemoryPlugin:
    """Plugin for spatial memory and navigation"""

    name = "spatial_memory"
    version = "1.0.0"
    description = "Store spatial information and support navigation tasks"
    author = "Windows AI Team"

    def __init__(self):
        self.locations = {}
        self.spatial_maps = {}
        self.routes = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Spatial Memory plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Spatial Memory plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Spatial Memory action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "add_location":
                return self._add_location(params)
            elif action == "recall_location":
                return self._recall_location(params)
            elif action == "find_nearby":
                return self._find_nearby(params)
            elif action == "create_route":
                return self._create_route(params)
            elif action == "navigate":
                return self._navigate(params)
            elif action == "create_cognitive_map":
                return self._create_cognitive_map(params)
            elif action == "spatial_reasoning":
                return self._spatial_reasoning(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _add_location(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a location to spatial memory"""
        location_id = params.get("location_id", f"loc_{len(self.locations)}")
        coordinates = params.get("coordinates", (0.0, 0.0))
        name = params.get("name", "")
        landmarks = params.get("landmarks", [])
        properties = params.get("properties", {})

        location = {
            "id": location_id,
            "name": name,
            "coordinates": coordinates,
            "landmarks": landmarks,
            "properties": properties,
            "visited_count": 0,
            "last_visited": "now",
            "connected_to": []
        }

        self.locations[location_id] = location

        return {
            "success": True,
            "location_id": location_id,
            "location": location,
            "total_locations": len(self.locations)
        }

    def _recall_location(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Recall a location from spatial memory"""
        location_id = params.get("location_id", "")
        name = params.get("name", "")

        location = None

        if location_id and location_id in self.locations:
            location = self.locations[location_id]
            location["visited_count"] += 1
            location["last_visited"] = "now"

        elif name:
            # Search by name
            for loc in self.locations.values():
                if loc["name"] == name:
                    location = loc
                    location["visited_count"] += 1
                    location["last_visited"] = "now"
                    break

        if location:
            return {
                "success": True,
                "location": location,
                "retrieval_method": "id" if location_id else "name"
            }
        else:
            return {"success": False, "error": "Location not found"}

    def _find_nearby(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find locations near a reference point"""
        reference = params.get("reference", (0.0, 0.0))
        radius = params.get("radius", 10.0)
        max_results = params.get("max_results", 5)

        nearby = []

        for location in self.locations.values():
            coords = location["coordinates"]
            distance = self._calculate_distance(reference, coords)

            if distance <= radius:
                nearby.append({
                    "location": location,
                    "distance": distance
                })

        # Sort by distance
        nearby.sort(key=lambda x: x["distance"])

        return {
            "success": True,
            "reference_point": reference,
            "radius": radius,
            "nearby_locations": nearby[:max_results],
            "num_found": len(nearby)
        }

    def _calculate_distance(self, point1: tuple, point2: tuple) -> float:
        """Calculate Euclidean distance between two points"""
        x1, y1 = point1
        x2, y2 = point2
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    def _create_route(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a route between locations"""
        route_id = params.get("route_id", f"route_{len(self.routes)}")
        start_id = params.get("start", "")
        end_id = params.get("end", "")
        waypoints = params.get("waypoints", [])

        if start_id not in self.locations or end_id not in self.locations:
            return {"success": False, "error": "Start or end location not found"}

        # Create route
        route_locations = [start_id] + waypoints + [end_id]
        total_distance = 0.0

        for i in range(len(route_locations) - 1):
            loc1 = self.locations[route_locations[i]]
            loc2 = self.locations[route_locations[i + 1]]
            total_distance += self._calculate_distance(loc1["coordinates"], loc2["coordinates"])

        route = {
            "id": route_id,
            "start": start_id,
            "end": end_id,
            "waypoints": waypoints,
            "locations": route_locations,
            "total_distance": total_distance,
            "created_at": "now"
        }

        self.routes[route_id] = route

        # Update connections
        for i in range(len(route_locations) - 1):
            loc_id = route_locations[i]
            next_loc = route_locations[i + 1]

            if next_loc not in self.locations[loc_id]["connected_to"]:
                self.locations[loc_id]["connected_to"].append(next_loc)

        return {
            "success": True,
            "route_id": route_id,
            "route": route,
            "num_waypoints": len(waypoints),
            "total_distance": total_distance
        }

    def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate from current location to destination"""
        current = params.get("current", "")
        destination = params.get("destination", "")
        strategy = params.get("strategy", "shortest")  # shortest, landmark

        if current not in self.locations or destination not in self.locations:
            return {"success": False, "error": "Current or destination location not found"}

        # Simple pathfinding (would use A* in production)
        if strategy == "shortest":
            path = self._find_shortest_path(current, destination)
        elif strategy == "landmark":
            path = self._find_landmark_path(current, destination)
        else:
            path = [current, destination]

        # Calculate total distance
        total_distance = 0.0
        for i in range(len(path) - 1):
            loc1 = self.locations[path[i]]
            loc2 = self.locations[path[i + 1]]
            total_distance += self._calculate_distance(loc1["coordinates"], loc2["coordinates"])

        # Generate turn-by-turn directions
        directions = []
        for i in range(len(path) - 1):
            from_loc = self.locations[path[i]]["name"]
            to_loc = self.locations[path[i + 1]]["name"]
            directions.append(f"Go from {from_loc} to {to_loc}")

        return {
            "success": True,
            "current": current,
            "destination": destination,
            "path": path,
            "total_distance": total_distance,
            "num_steps": len(path) - 1,
            "directions": directions,
            "strategy": strategy
        }

    def _find_shortest_path(self, start: str, end: str) -> List[str]:
        """Find shortest path (simplified)"""
        # In production, would use Dijkstra or A*
        return [start, end]

    def _find_landmark_path(self, start: str, end: str) -> List[str]:
        """Find path using landmarks"""
        # Find locations with landmarks between start and end
        path = [start]

        for loc_id, location in self.locations.items():
            if loc_id != start and loc_id != end and location["landmarks"]:
                path.append(loc_id)

        path.append(end)
        return path

    def _create_cognitive_map(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a cognitive map of explored space"""
        map_id = params.get("map_id", f"map_{len(self.spatial_maps)}")
        location_ids = params.get("locations", list(self.locations.keys()))

        cognitive_map = {
            "id": map_id,
            "locations": {},
            "regions": [],
            "boundaries": {},
            "landmarks": []
        }

        # Add locations to map
        for loc_id in location_ids:
            if loc_id in self.locations:
                cognitive_map["locations"][loc_id] = self.locations[loc_id]

        # Identify regions (clusters of nearby locations)
        regions = self._identify_regions(location_ids)
        cognitive_map["regions"] = regions

        # Identify prominent landmarks
        for loc_id in location_ids:
            if loc_id in self.locations and self.locations[loc_id]["landmarks"]:
                cognitive_map["landmarks"].extend(self.locations[loc_id]["landmarks"])

        self.spatial_maps[map_id] = cognitive_map

        return {
            "success": True,
            "map_id": map_id,
            "cognitive_map": cognitive_map,
            "num_locations": len(cognitive_map["locations"]),
            "num_regions": len(regions)
        }

    def _identify_regions(self, location_ids: List[str]) -> List[Dict]:
        """Identify spatial regions from locations"""
        # Simplified clustering
        regions = [{
            "region_id": "region_1",
            "center": (0.0, 0.0),
            "radius": 20.0,
            "locations": location_ids[:len(location_ids)//2]
        }, {
            "region_id": "region_2",
            "center": (50.0, 50.0),
            "radius": 20.0,
            "locations": location_ids[len(location_ids)//2:]
        }]

        return regions

    def _spatial_reasoning(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform spatial reasoning tasks"""
        task_type = params.get("type", "relative_position")
        location_a = params.get("location_a", "")
        location_b = params.get("location_b", "")

        if location_a not in self.locations or location_b not in self.locations:
            return {"success": False, "error": "Locations not found"}

        loc_a = self.locations[location_a]
        loc_b = self.locations[location_b]

        result = {}

        if task_type == "relative_position":
            # Determine relative position
            x1, y1 = loc_a["coordinates"]
            x2, y2 = loc_b["coordinates"]

            if x2 > x1:
                result["horizontal"] = "east"
            elif x2 < x1:
                result["horizontal"] = "west"
            else:
                result["horizontal"] = "same"

            if y2 > y1:
                result["vertical"] = "north"
            elif y2 < y1:
                result["vertical"] = "south"
            else:
                result["vertical"] = "same"

        elif task_type == "distance":
            result["distance"] = self._calculate_distance(
                loc_a["coordinates"],
                loc_b["coordinates"]
            )

        elif task_type == "direction":
            # Calculate bearing
            x1, y1 = loc_a["coordinates"]
            x2, y2 = loc_b["coordinates"]
            angle = math.atan2(y2 - y1, x2 - x1) * 180 / math.pi
            result["bearing"] = angle
            result["cardinal_direction"] = self._angle_to_cardinal(angle)

        return {
            "success": True,
            "task_type": task_type,
            "location_a": location_a,
            "location_b": location_b,
            "result": result
        }

    def _angle_to_cardinal(self, angle: float) -> str:
        """Convert angle to cardinal direction"""
        if -22.5 <= angle < 22.5:
            return "E"
        elif 22.5 <= angle < 67.5:
            return "NE"
        elif 67.5 <= angle < 112.5:
            return "N"
        elif 112.5 <= angle < 157.5:
            return "NW"
        elif angle >= 157.5 or angle < -157.5:
            return "W"
        elif -157.5 <= angle < -112.5:
            return "SW"
        elif -112.5 <= angle < -67.5:
            return "S"
        else:
            return "SE"

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.locations = {}
        self.spatial_maps = {}
        self.routes = {}
        return True
