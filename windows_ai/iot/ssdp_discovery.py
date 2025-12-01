"""
SSDP/UPnP Device Discovery
Discovers UPnP devices using Simple Service Discovery Protocol
"""
from typing import Dict, Any, List, Callable, Optional
import logging
import socket
import threading
import time
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not available. Install with: pip install requests")


class SSDPDiscovery:
    """
    SSDP/UPnP device discovery
    Discovers devices using Simple Service Discovery Protocol
    """

    # SSDP multicast group and port
    SSDP_ADDR = "239.255.255.250"
    SSDP_PORT = 1900

    # Common UPnP device types
    DEVICE_TYPES = [
        "ssdp:all",                          # All devices
        "upnp:rootdevice",                   # Root devices
        "urn:schemas-upnp-org:device:MediaRenderer:1",  # Media renderers
        "urn:schemas-upnp-org:device:MediaServer:1",    # Media servers
        "urn:schemas-upnp-org:device:InternetGatewayDevice:1",  # Routers
        "urn:schemas-upnp-org:device:Basic:1",          # Basic devices
        "urn:dial-multiscreen-org:service:dial:1",      # DIAL (Chromecast)
        "urn:samsung.com:device:RemoteControlReceiver:1",  # Samsung TVs
    ]

    def __init__(self):
        self.is_available = True  # SSDP uses standard sockets
        self.scanning = False
        self.scan_thread = None
        self.discovered_devices = {}

    def start_scan(self, callback: Callable,
                   device_types: List[str] = None,
                   duration: int = 5) -> Dict[str, Any]:
        """
        Start SSDP device discovery

        Args:
            callback: Callback function(device) for each discovery
            device_types: List of device types to discover
            duration: Scan duration in seconds

        Returns:
            Dict with scan status
        """
        if self.scanning:
            return {
                "status": "error",
                "message": "Scan already in progress"
            }

        try:
            # Use default device types if not specified
            if device_types is None:
                device_types = ["ssdp:all"]

            self.scanning = True
            self.discovered_devices.clear()

            # Start scan in background thread
            self.scan_thread = threading.Thread(
                target=self._scan_network,
                args=(callback, device_types, duration),
                daemon=True
            )
            self.scan_thread.start()

            logger.info(f"SSDP scan started for {len(device_types)} device types")

            return {
                "status": "success",
                "message": "SSDP scan started",
                "device_types": len(device_types),
                "duration": duration
            }

        except Exception as e:
            logger.error(f"SSDP scan error: {e}")
            self.scanning = False
            return {"status": "error", "message": str(e)}

    def stop_scan(self) -> Dict[str, Any]:
        """Stop SSDP discovery"""
        if not self.scanning:
            return {
                "status": "error",
                "message": "No scan in progress"
            }

        self.scanning = False

        # Wait for scan thread to finish
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=2)

        logger.info("SSDP scan stopped")

        return {
            "status": "success",
            "message": "SSDP scan stopped",
            "discovered": len(self.discovered_devices)
        }

    def _scan_network(self, callback: Callable,
                     device_types: List[str],
                     duration: int):
        """Scan network for SSDP devices"""
        try:
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1.0)

            # Send M-SEARCH for each device type
            for device_type in device_types:
                if not self.scanning:
                    break

                message = self._create_msearch_message(device_type)

                try:
                    sock.sendto(message.encode('utf-8'),
                               (self.SSDP_ADDR, self.SSDP_PORT))
                except Exception as e:
                    logger.error(f"Error sending M-SEARCH: {e}")

            # Listen for responses
            start_time = time.time()
            while self.scanning and (time.time() - start_time) < duration:
                try:
                    data, addr = sock.recvfrom(4096)
                    response = data.decode('utf-8', errors='ignore')

                    # Parse response
                    device = self._parse_ssdp_response(response, addr)
                    if device:
                        device_id = device.device_id

                        # Avoid duplicates
                        if device_id not in self.discovered_devices:
                            self.discovered_devices[device_id] = device
                            callback(device)

                except socket.timeout:
                    continue
                except Exception as e:
                    logger.debug(f"SSDP receive error: {e}")

            sock.close()

        except Exception as e:
            logger.error(f"SSDP scan error: {e}")
        finally:
            self.scanning = False

    def _create_msearch_message(self, search_target: str) -> str:
        """Create SSDP M-SEARCH message"""
        return (
            "M-SEARCH * HTTP/1.1\r\n"
            f"HOST: {self.SSDP_ADDR}:{self.SSDP_PORT}\r\n"
            "MAN: \"ssdp:discover\"\r\n"
            "MX: 3\r\n"
            f"ST: {search_target}\r\n"
            "\r\n"
        )

    def _parse_ssdp_response(self, response: str, addr: tuple) -> Optional[object]:
        """Parse SSDP response"""
        try:
            from .discovery import DiscoveredDevice

            # Parse headers
            headers = {}
            for line in response.split('\r\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()

            # Extract information
            location = headers.get('location', '')
            usn = headers.get('usn', '')
            server = headers.get('server', '')
            st = headers.get('st', '')

            # Parse USN for device info
            device_uuid = ''
            if 'uuid:' in usn:
                uuid_match = re.search(r'uuid:([^:]+)', usn)
                if uuid_match:
                    device_uuid = uuid_match.group(1)

            # Get device description if available
            device_info = {}
            if location and REQUESTS_AVAILABLE:
                device_info = self._fetch_device_description(location)

            # Create device
            device = DiscoveredDevice(
                device_id=f"ssdp_{device_uuid}" if device_uuid else f"ssdp_{addr[0]}",
                device_type="unknown",  # Will be categorized
                name=device_info.get('friendlyName', f"SSDP Device {addr[0]}"),
                protocol="ssdp",
                ip_address=addr[0],
                manufacturer=device_info.get('manufacturer'),
                model=device_info.get('modelName'),
                firmware_version=device_info.get('modelNumber'),
                service_type=st,
                metadata={
                    'location': location,
                    'usn': usn,
                    'server': server,
                    'st': st,
                    **device_info
                }
            )

            return device

        except Exception as e:
            logger.debug(f"Error parsing SSDP response: {e}")
            return None

    def _fetch_device_description(self, location: str) -> Dict[str, Any]:
        """Fetch device description XML"""
        try:
            response = requests.get(location, timeout=2)
            if response.status_code == 200:
                return self._parse_device_xml(response.text)
        except Exception as e:
            logger.debug(f"Error fetching device description: {e}")
        return {}

    def _parse_device_xml(self, xml: str) -> Dict[str, Any]:
        """Parse UPnP device description XML"""
        info = {}

        try:
            # Simple regex parsing (could use xml.etree for production)
            patterns = {
                'friendlyName': r'<friendlyName>([^<]+)</friendlyName>',
                'manufacturer': r'<manufacturer>([^<]+)</manufacturer>',
                'manufacturerURL': r'<manufacturerURL>([^<]+)</manufacturerURL>',
                'modelName': r'<modelName>([^<]+)</modelName>',
                'modelNumber': r'<modelNumber>([^<]+)</modelNumber>',
                'modelDescription': r'<modelDescription>([^<]+)</modelDescription>',
                'serialNumber': r'<serialNumber>([^<]+)</serialNumber>',
                'UDN': r'<UDN>([^<]+)</UDN>',
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, xml)
                if match:
                    info[key] = match.group(1).strip()

        except Exception as e:
            logger.debug(f"Error parsing device XML: {e}")

        return info

    def discover_upnp_devices(self, timeout: int = 5) -> Dict[str, Any]:
        """
        Discover all UPnP devices

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            Dict with discovered devices
        """
        discovered = []

        def on_discovery(device):
            discovered.append(device)

        # Start scan
        self.start_scan(on_discovery, duration=timeout)

        # Wait for scan to complete
        time.sleep(timeout + 1)

        return {
            "status": "success",
            "devices": [d.to_dict() for d in discovered],
            "count": len(discovered)
        }

    def get_status(self) -> Dict[str, Any]:
        """Get scanner status"""
        return {
            "status": "success",
            "available": self.is_available,
            "scanning": self.scanning,
            "discovered": len(self.discovered_devices)
        }
