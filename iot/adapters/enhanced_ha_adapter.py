#!/usr/bin/env python3
"""
Enhanced Home Assistant Adapter with Full Device Support
Auto-integrates with all discovered devices from Gemini's setup
"""
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import requests

logger = logging.getLogger(__name__)


class EnhancedHAAdapter:
    """Enhanced Home Assistant adapter with full automation"""
    
    def __init__(self, base_url: str = None, token: str = None):
        # Try to load from config or environment
        self.workspace = Path("C:/Users/antho")
        self.config = self._load_config()
        
        self.base_url = (base_url or self.config.get("ha_url", "")).rstrip('/')
        self.token = token or self.config.get("ha_token", "")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        } if self.token else {}
        
        self.device_registry = self.workspace / "ha_device_registry.json"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load Home Assistant config"""
        config_file = self.workspace / "ha_config.json"
        if config_file.exists():
            return json.loads(config_file.read_text())
        return {}
    
    def sync_from_registry(self) -> List[Dict[str, Any]]:
        """Sync all devices from Gemini's registry"""
        if self.device_registry.exists():
            data = json.loads(self.device_registry.read_text())
            devices = data.get("devices", [])
            logger.info(f"Synced {len(devices)} devices from registry")
            return devices
        return []
    
    def discover_all_devices(self) -> Dict[str, Any]:
        """Discover all Home Assistant devices"""
        if not self.base_url or not self.token:
            logger.warning("HA connection not configured, using registry only")
            return {"status": "registry_only", "devices": self.sync_from_registry()}
        
        try:
            response = requests.get(
                f"{self.base_url}/api/states",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            entities = response.json()
            categorized = self._categorize_entities(entities)
            
            logger.info(f"Discovered {len(entities)} entities")
            return {
                "status": "success",
                "total": len(entities),
                "categorized": categorized,
                "entities": entities
            }
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _categorize_entities(self, entities: List[Dict]) -> Dict[str, List]:
        """Categorize entities by domain"""
        categorized = {}
        for entity in entities:
            domain = entity.get("entity_id", "").split(".")[0]
            if domain not in categorized:
                categorized[domain] = []
            categorized[domain].append(entity)
        return categorized
    
    def create_automation(self, name: str, trigger: Dict, action: Dict) -> Dict[str, Any]:
        """Create Home Assistant automation"""
        if not self.base_url:
            return {"status": "not_configured"}
        
        try:
            automation = {
                "alias": name,
                "trigger": trigger,
                "action": action
            }
            
            response = requests.post(
                f"{self.base_url}/api/config/automation/config/{name}",
                headers=self.headers,
                json=automation,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Created automation: {name}")
            return {"status": "success", "automation": name}
        except Exception as e:
            logger.error(f"Automation creation failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def bulk_control(self, entity_ids: List[str], action: str, **kwargs) -> Dict[str, Any]:
        """Control multiple entities at once"""
        results = []
        for entity_id in entity_ids:
            domain = entity_id.split(".")[0]
            result = self.call_service(domain, action, entity_id, **kwargs)
            results.append({"entity_id": entity_id, "result": result})
        
        return {
            "status": "success",
            "controlled": len(entity_ids),
            "results": results
        }
    
    def call_service(self, domain: str, service: str, entity_id: str = None, **kwargs):
        """Call Home Assistant service"""
        if not self.base_url:
            return {"status": "not_configured"}
        
        try:
            data = {"entity_id": entity_id} if entity_id else {}
            data.update(kwargs)
            
            response = requests.post(
                f"{self.base_url}/api/services/{domain}/{service}",
                headers=self.headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return {"status": "success"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_area_devices(self, area_name: str) -> List[Dict[str, Any]]:
        """Get all devices in a specific area"""
        devices = self.sync_from_registry()
        return [d for d in devices if d.get("area") == area_name]
    
    def create_scene(self, name: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Create a scene with entity states"""
        if not self.base_url:
            return {"status": "not_configured"}
        
        try:
            scene_data = {
                "name": name,
                "entities": entities
            }
            
            result = self.call_service("scene", "create", **scene_data)
            logger.info(f"Created scene: {name}")
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}


def main():
    """Test the enhanced adapter"""
    adapter = EnhancedHAAdapter()
    
    print("🔍 Syncing devices from Gemini's registry...")
    devices = adapter.sync_from_registry()
    print(f"✓ Found {len(devices)} devices")
    
    if devices:
        print("\nRegistered Devices:")
        for device in devices[:10]:  # Show first 10
            print(f"  • {device.get('name', 'Unknown')} ({device.get('type', 'unknown')})")


if __name__ == "__main__":
    main()
