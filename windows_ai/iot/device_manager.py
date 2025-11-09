"""
IoT Device Manager Module
Device discovery, registration, and management
"""
from typing import Dict, Any, List, Optional
import logging
import json
import time
import socket

logger = logging.getLogger(__name__)


class Device:
    """IoT Device representation"""

    def __init__(self, device_id: str, device_type: str, **kwargs):
        self.device_id = device_id
        self.device_type = device_type
        self.name = kwargs.get("name", device_id)
        self.location = kwargs.get("location")
        self.ip_address = kwargs.get("ip_address")
        self.mac_address = kwargs.get("mac_address")
        self.firmware_version = kwargs.get("firmware_version")
        self.capabilities = kwargs.get("capabilities", [])
        self.metadata = kwargs.get("metadata", {})
        self.status = "unknown"
        self.last_seen = None
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert device to dictionary"""
        return {
            "device_id": self.device_id,
            "device_type": self.device_type,
            "name": self.name,
            "location": self.location,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "firmware_version": self.firmware_version,
            "capabilities": self.capabilities,
            "metadata": self.metadata,
            "status": self.status,
            "last_seen": self.last_seen,
            "created_at": self.created_at
        }

    def update_status(self, status: str):
        """Update device status"""
        self.status = status
        self.last_seen = time.time()


class DeviceManager:
    """Production IoT device management"""

    def __init__(self):
        self.devices = {}
        self.device_groups = {}

    def register_device(self, device_id: str, device_type: str, **kwargs) -> Dict[str, Any]:
        """
        Register a new IoT device

        Args:
            device_id: Unique device identifier
            device_type: Type of device (sensor, actuator, gateway, etc.)
            name: Human-readable name
            location: Physical location
            ip_address: Device IP address
            mac_address: Device MAC address
            capabilities: List of device capabilities
            metadata: Additional device metadata

        Returns:
            Dict with registration status
        """
        try:
            if device_id in self.devices:
                return {
                    "status": "error",
                    "message": f"Device already registered: {device_id}"
                }

            device = Device(device_id, device_type, **kwargs)
            self.devices[device_id] = device

            logger.info(f"Registered device: {device_id} ({device_type})")

            return {
                "status": "success",
                "message": "Device registered",
                "device": device.to_dict()
            }

        except Exception as e:
            logger.error(f"Register device error: {e}")
            return {"status": "error", "message": str(e)}

    def unregister_device(self, device_id: str) -> Dict[str, Any]:
        """Unregister device"""
        if device_id not in self.devices:
            return {
                "status": "error",
                "message": f"Device not found: {device_id}"
            }

        del self.devices[device_id]

        return {
            "status": "success",
            "message": "Device unregistered",
            "device_id": device_id
        }

    def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get device information"""
        if device_id not in self.devices:
            return {
                "status": "error",
                "message": f"Device not found: {device_id}"
            }

        return {
            "status": "success",
            "device": self.devices[device_id].to_dict()
        }

    def list_devices(self, device_type: str = None,
                    status: str = None) -> Dict[str, Any]:
        """
        List registered devices

        Args:
            device_type: Filter by device type
            status: Filter by status

        Returns:
            Dict with device list
        """
        devices = []

        for device in self.devices.values():
            # Apply filters
            if device_type and device.device_type != device_type:
                continue
            if status and device.status != status:
                continue

            devices.append(device.to_dict())

        return {
            "status": "success",
            "devices": devices,
            "count": len(devices)
        }

    def update_device_status(self, device_id: str, status: str) -> Dict[str, Any]:
        """Update device status"""
        if device_id not in self.devices:
            return {
                "status": "error",
                "message": f"Device not found: {device_id}"
            }

        self.devices[device_id].update_status(status)

        return {
            "status": "success",
            "message": "Status updated",
            "device_id": device_id,
            "new_status": status
        }

    def create_device_group(self, group_name: str, device_ids: List[str],
                           description: str = None) -> Dict[str, Any]:
        """
        Create device group

        Args:
            group_name: Name of the group
            device_ids: List of device IDs to include
            description: Group description

        Returns:
            Dict with group creation status
        """
        if group_name in self.device_groups:
            return {
                "status": "error",
                "message": f"Group already exists: {group_name}"
            }

        # Validate device IDs
        for device_id in device_ids:
            if device_id not in self.devices:
                return {
                    "status": "error",
                    "message": f"Device not found: {device_id}"
                }

        self.device_groups[group_name] = {
            "name": group_name,
            "description": description,
            "device_ids": device_ids,
            "created_at": time.time()
        }

        return {
            "status": "success",
            "message": "Group created",
            "group": self.device_groups[group_name]
        }

    def add_device_to_group(self, group_name: str, device_id: str) -> Dict[str, Any]:
        """Add device to group"""
        if group_name not in self.device_groups:
            return {
                "status": "error",
                "message": f"Group not found: {group_name}"
            }

        if device_id not in self.devices:
            return {
                "status": "error",
                "message": f"Device not found: {device_id}"
            }

        if device_id in self.device_groups[group_name]["device_ids"]:
            return {
                "status": "error",
                "message": f"Device already in group"
            }

        self.device_groups[group_name]["device_ids"].append(device_id)

        return {
            "status": "success",
            "message": "Device added to group",
            "group": group_name,
            "device_id": device_id
        }

    def get_group_devices(self, group_name: str) -> Dict[str, Any]:
        """Get devices in a group"""
        if group_name not in self.device_groups:
            return {
                "status": "error",
                "message": f"Group not found: {group_name}"
            }

        device_ids = self.device_groups[group_name]["device_ids"]
        devices = [
            self.devices[device_id].to_dict()
            for device_id in device_ids
            if device_id in self.devices
        ]

        return {
            "status": "success",
            "group": group_name,
            "devices": devices,
            "count": len(devices)
        }

    def discover_devices(self, scan_network: bool = False) -> Dict[str, Any]:
        """
        Discover devices on network

        Args:
            scan_network: Perform network scan

        Returns:
            Dict with discovered devices
        """
        discovered = []

        if scan_network:
            # Basic network scan for common IoT ports
            discovered = self._scan_network()

        return {
            "status": "success",
            "discovered": discovered,
            "count": len(discovered)
        }

    def _scan_network(self, timeout: float = 1.0) -> List[Dict[str, Any]]:
        """Scan local network for devices"""
        discovered = []

        # Common IoT device ports
        ports = [
            80,    # HTTP
            443,   # HTTPS
            1883,  # MQTT
            8883,  # MQTT SSL
            8080,  # HTTP Alt
            5683,  # CoAP
        ]

        # Get local network range (simplified)
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            network_prefix = '.'.join(local_ip.split('.')[:-1])

            # Scan a small range (last 10 IPs as example)
            for i in range(1, 11):
                ip = f"{network_prefix}.{i}"

                for port in ports:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(timeout)

                    result = sock.connect_ex((ip, port))
                    if result == 0:
                        discovered.append({
                            "ip": ip,
                            "port": port,
                            "status": "open"
                        })

                    sock.close()

        except Exception as e:
            logger.error(f"Network scan error: {e}")

        return discovered

    def get_device_statistics(self) -> Dict[str, Any]:
        """Get device statistics"""
        stats = {
            "total_devices": len(self.devices),
            "by_type": {},
            "by_status": {},
            "groups": len(self.device_groups)
        }

        for device in self.devices.values():
            # Count by type
            stats["by_type"][device.device_type] = stats["by_type"].get(device.device_type, 0) + 1

            # Count by status
            stats["by_status"][device.status] = stats["by_status"].get(device.status, 0) + 1

        return {
            "status": "success",
            "statistics": stats
        }

    def export_devices(self, file_path: str = None) -> Dict[str, Any]:
        """Export device registry to JSON"""
        try:
            data = {
                "devices": [device.to_dict() for device in self.devices.values()],
                "groups": self.device_groups,
                "exported_at": time.time()
            }

            if file_path:
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)

                return {
                    "status": "success",
                    "message": "Devices exported",
                    "file_path": file_path
                }
            else:
                return {
                    "status": "success",
                    "data": data
                }

        except Exception as e:
            logger.error(f"Export devices error: {e}")
            return {"status": "error", "message": str(e)}

    def import_devices(self, file_path: str) -> Dict[str, Any]:
        """Import device registry from JSON"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            imported_count = 0
            for device_data in data.get("devices", []):
                device_id = device_data["device_id"]
                if device_id not in self.devices:
                    device = Device(**device_data)
                    self.devices[device_id] = device
                    imported_count += 1

            # Import groups
            for group_name, group_data in data.get("groups", {}).items():
                if group_name not in self.device_groups:
                    self.device_groups[group_name] = group_data

            return {
                "status": "success",
                "message": "Devices imported",
                "imported_devices": imported_count,
                "imported_groups": len(data.get("groups", {}))
            }

        except Exception as e:
            logger.error(f"Import devices error: {e}")
            return {"status": "error", "message": str(e)}
