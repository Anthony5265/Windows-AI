"""
Windows-AI Plugin Registry
Central registry for all plugins and integrations
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class PluginRegistry:
    """
    Central registry for all Windows-AI plugins
    """
    
    def __init__(self, plugins_root: Path = None):
        self.plugins_root = plugins_root or Path(__file__).parent
        self.registry = self._scan_plugins()
    
    def _scan_plugins(self) -> Dict[str, List[Dict]]:
        """Scan all plugin directories and build registry"""
        registry = {
            "ai_providers": [],
            "local_models": [],
            "code_models": [],
            "vision_models": [],
            "audio_models": [],
            "windows_integration": [],
            "web_integration": [],
            "developer_tools": [],
        }
        
        # Scan each category
        for category in registry.keys():
            category_dir = self.plugins_root / category
            if not category_dir.exists():
                continue
            
            for plugin_dir in category_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue
                
                config_file = plugin_dir / "config.json"
                if config_file.exists():
                    try:
                        with open(config_file) as f:
                            config = json.load(f)
                            config["path"] = str(plugin_dir)
                            registry[category].append(config)
                    except Exception as e:
                        print(f"Error loading {config_file}: {e}")
        
        return registry
    
    def get_plugin(self, category: str, name: str) -> Optional[Dict]:
        """Get plugin configuration by category and name"""
        if category not in self.registry:
            return None
        
        for plugin in self.registry[category]:
            if plugin.get("name", "").lower() == name.lower():
                return plugin
        
        return None
    
    def list_plugins(self, category: Optional[str] = None) -> List[Dict]:
        """List all plugins or plugins in a category"""
        if category:
            return self.registry.get(category, [])
        
        # Return all plugins
        all_plugins = []
        for plugins in self.registry.values():
            all_plugins.extend(plugins)
        return all_plugins
    
    def get_stats(self) -> Dict[str, int]:
        """Get plugin statistics"""
        stats = {}
        for category, plugins in self.registry.items():
            stats[category] = len(plugins)
        stats["total"] = sum(stats.values())
        return stats
    
    def search(self, query: str) -> List[Dict]:
        """Search plugins by name or feature"""
        query = query.lower()
        results = []
        
        for plugins in self.registry.values():
            for plugin in plugins:
                if query in plugin.get("name", "").lower():
                    results.append(plugin)
                elif "features" in plugin and any(query in f.lower() for f in plugin["features"]):
                    results.append(plugin)
        
        return results


def main():
    """Display registry statistics"""
    registry = PluginRegistry()
    stats = registry.get_stats()
    
    print("=" * 80)
    print("WINDOWS-AI PLUGIN REGISTRY")
    print("=" * 80)
    print()
    
    print("Plugin Statistics:")
    for category, count in sorted(stats.items()):
        if category != "total":
            print(f"  {category:30s}: {count:3d} plugins")
    
    print(f"\n  {'TOTAL':30s}: {stats['total']:3d} plugins")
    
    print("\n" + "=" * 80)
    
    # Show some examples
    print("\nAI Providers:")
    for plugin in registry.list_plugins("ai_providers")[:5]:
        print(f"  - {plugin['name']}")
    print(f"  ... and {len(registry.list_plugins('ai_providers')) - 5} more")
    
    print("\nLocal Models:")
    for plugin in registry.list_plugins("local_models")[:5]:
        print(f"  - {plugin['name']}")
    
    print("\nCode Models:")
    for plugin in registry.list_plugins("code_models"):
        print(f"  - {plugin['name']}")


if __name__ == "__main__":
    main()
