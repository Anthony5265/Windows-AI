"""
IoT Device Discovery Module
Unified device discovery using multiple protocols (mDNS, SSDP, BLE)
"""
from typing import Dict, Any, List, Optional, Callable
import logging
import threading
import time
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredDevice:
    """Discovered device information"""
    device_id: str
    device_type: str
    name: str
    protocol: str  # mdns, ssdp, ble, http
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    port: Optional[int] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    capabilities: List[str] = None
    service_type: Optional[str] = None
    metadata: Dict[str, Any] = None
    rssi: Optional[int] = None  # Signal strength for BLE
    discovered_at: float = None

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.metadata is None:
            self.metadata = {}
        if self.discovered_at is None:
            self.discovered_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class DeviceDiscovery:
    """
    Unified device discovery manager
    Coordinates multiple discovery protocols
    """

    def __init__(self):
        self.discovered_devices = {}
        self.discovery_callbacks = []
        self.active_scanners = {}
        self.scan_thread = None
        self.scanning = False

        # Import discovery modules
        self._init_mdns()
        self._init_ssdp()
        self._init_ble()

    def _init_mdns(self):
        """Initialize mDNS discovery"""
        try:
            from .mdns_discovery import MDNSDiscovery
            self.mdns = MDNSDiscovery()
            logger.info("mDNS discovery initialized")
        except Exception as e:
            logger.warning(f"mDNS discovery not available: {e}")
            self.mdns = None

    def _init_ssdp(self):
        """Initialize SSDP discovery"""
        try:
            from .ssdp_discovery import SSDPDiscovery
            self.ssdp = SSDPDiscovery()
            logger.info("SSDP discovery initialized")
        except Exception as e:
            logger.warning(f"SSDP discovery not available: {e}")
            self.ssdp = None

    def _init_ble(self):
        """Initialize BLE scanner"""
        try:
            from .ble_scanner import BLEScanner
            self.ble = BLEScanner()
            logger.info("BLE scanner initialized")
        except Exception as e:
            logger.warning(f"BLE scanner not available: {e}")
            self.ble = None

    def start_discovery(self, protocols: List[str] = None,
                       duration: int = 30,
                       callback: Callable = None) -> Dict[str, Any]:
        """
        Start device discovery

        Args:
            protocols: List of protocols to use ['mdns', 'ssdp', 'ble']
                      If None, uses all available
            duration: Discovery duration in seconds (0 for continuous)
            callback: Optional callback function(device) for each discovery

        Returns:
            Dict with discovery status
        """
        if self.scanning:
            return {
                "status": "error",
                "message": "Discovery already in progress"
            }

        # Determine which protocols to use
        if protocols is None:
            protocols = []
            if self.mdns: protocols.append('mdns')
            if self.ssdp: protocols.append('ssdp')
            if self.ble: protocols.append('ble')

        if not protocols:
            return {
                "status": "error",
                "message": "No discovery protocols available"
            }

        # Add callback if provided
        if callback:
            self.discovery_callbacks.append(callback)

        # Start discovery
        self.scanning = True
        self.discovered_devices.clear()

        logger.info(f"Starting discovery with protocols: {protocols}")

        # Start each protocol scanner
        if 'mdns' in protocols and self.mdns:
            self.mdns.start_scan(self._on_device_discovered)

        if 'ssdp' in protocols and self.ssdp:
            self.ssdp.start_scan(self._on_device_discovered)

        if 'ble' in protocols and self.ble:
            self.ble.start_scan(self._on_device_discovered)

        # Auto-stop after duration
        if duration > 0:
            def stop_after_duration():
                time.sleep(duration)
                self.stop_discovery()

            stop_thread = threading.Thread(target=stop_after_duration, daemon=True)
            stop_thread.start()

        return {
            "status": "success",
            "message": "Discovery started",
            "protocols": protocols,
            "duration": duration if duration > 0 else "continuous"
        }

    def stop_discovery(self) -> Dict[str, Any]:
        """Stop device discovery"""
        if not self.scanning:
            return {
                "status": "error",
                "message": "Discovery not in progress"
            }

        logger.info("Stopping discovery")

        # Stop all scanners
        if self.mdns:
            self.mdns.stop_scan()
        if self.ssdp:
            self.ssdp.stop_scan()
        if self.ble:
            self.ble.stop_scan()

        self.scanning = False

        return {
            "status": "success",
            "message": "Discovery stopped",
            "discovered_count": len(self.discovered_devices)
        }

    def _on_device_discovered(self, device: DiscoveredDevice):
        """Internal callback for device discovery"""
        device_id = device.device_id

        # Store device
        self.discovered_devices[device_id] = device

        # Call user callbacks
        for callback in self.discovery_callbacks:
            try:
                callback(device)
            except Exception as e:
                logger.error(f"Discovery callback error: {e}")

        logger.info(f"Discovered device: {device.name} ({device.protocol})")

    def get_discovered_devices(self, protocol: str = None,
                               device_type: str = None) -> Dict[str, Any]:
        """
        Get discovered devices with optional filtering

        Args:
            protocol: Filter by protocol (mdns, ssdp, ble)
            device_type: Filter by device type

        Returns:
            Dict with device list
        """
        devices = list(self.discovered_devices.values())

        # Apply filters
        if protocol:
            devices = [d for d in devices if d.protocol == protocol]
        if device_type:
            devices = [d for d in devices if d.device_type == device_type]

        return {
            "status": "success",
            "devices": [d.to_dict() for d in devices],
            "count": len(devices),
            "scanning": self.scanning
        }

    def discover_specific_device(self, device_id: str = None,
                                 service_type: str = None,
                                 timeout: int = 10) -> Dict[str, Any]:
        """
        Discover a specific device or service type

        Args:
            device_id: Specific device ID to find
            service_type: Service type to discover
            timeout: Discovery timeout in seconds

        Returns:
            Dict with device information
        """
        found_device = None

        def on_found(device):
            nonlocal found_device
            if device_id and device.device_id == device_id:
                found_device = device
            elif service_type and device.service_type == service_type:
                found_device = device

        # Start discovery
        self.start_discovery(callback=on_found, duration=timeout)

        # Wait for timeout
        start_time = time.time()
        while (time.time() - start_time) < timeout and not found_device:
            time.sleep(0.5)

        # Stop discovery
        self.stop_discovery()

        if found_device:
            return {
                "status": "success",
                "device": found_device.to_dict()
            }
        else:
            return {
                "status": "error",
                "message": "Device not found"
            }

    def categorize_device(self, device: DiscoveredDevice) -> str:
        """
        Automatically categorize device based on metadata

        Returns:
            Device category (light, sensor, camera, speaker, etc.)
        """
        name_lower = device.name.lower()
        service_type = device.service_type or ""
        service_lower = service_type.lower()

        # Light devices
        if any(keyword in name_lower for keyword in ['light', 'lamp', 'bulb', 'hue']):
            return 'light'
        if 'lighting' in service_lower:
            return 'light'

        # Cameras
        if any(keyword in name_lower for keyword in ['camera', 'cam', 'nest cam', 'ring', 'wyze']):
            return 'camera'
        if 'camera' in service_lower or 'rtsp' in service_lower:
            return 'camera'

        # Sensors
        if any(keyword in name_lower for keyword in ['sensor', 'motion', 'temperature', 'humidity']):
            return 'sensor'
        if 'sensor' in service_lower:
            return 'sensor'

        # Speakers/Audio
        if any(keyword in name_lower for keyword in ['speaker', 'sonos', 'audio', 'airplay']):
            return 'speaker'
        if 'audio' in service_lower or 'airplay' in service_lower:
            return 'speaker'

        # Smart plugs/switches
        if any(keyword in name_lower for keyword in ['plug', 'switch', 'outlet']):
            return 'switch'

        # Thermostats
        if any(keyword in name_lower for keyword in ['thermostat', 'nest', 'ecobee']):
            return 'thermostat'

        # Doorbells
        if 'doorbell' in name_lower or 'ring' in name_lower:
            return 'doorbell'

        # Smart displays
        if any(keyword in name_lower for keyword in ['display', 'hub', 'echo show']):
            return 'display'

        # Printers
        if 'printer' in name_lower or 'ipp' in service_lower:
            return 'printer'

        # Default
        return 'unknown'

    def get_discovery_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        stats = {
            "total_discovered": len(self.discovered_devices),
            "by_protocol": {},
            "by_type": {},
            "scanning": self.scanning
        }

        for device in self.discovered_devices.values():
            # Count by protocol
            protocol = device.protocol
            stats["by_protocol"][protocol] = stats["by_protocol"].get(protocol, 0) + 1

            # Count by type
            device_type = device.device_type
            stats["by_type"][device_type] = stats["by_type"].get(device_type, 0) + 1

        return {
            "status": "success",
            "statistics": stats
        }
