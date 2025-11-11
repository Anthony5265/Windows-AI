"""
mDNS/Bonjour Device Discovery
Discovers devices using multicast DNS (Zeroconf/Bonjour)
"""
from typing import Dict, Any, List, Callable, Optional
import logging
import socket
import threading

logger = logging.getLogger(__name__)

try:
    from zeroconf import Zeroconf, ServiceBrowser, ServiceListener
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False
    logger.warning("zeroconf not available. Install with: pip install zeroconf")


class MDNSServiceListener(ServiceListener):
    """Listener for mDNS service discovery"""

    def __init__(self, callback: Callable):
        self.callback = callback
        self.zeroconf = None

    def add_service(self, zc: Zeroconf, service_type: str, name: str):
        """Called when a service is discovered"""
        info = zc.get_service_info(service_type, name)
        if info:
            self._process_service(info, service_type)

    def update_service(self, zc: Zeroconf, service_type: str, name: str):
        """Called when a service is updated"""
        info = zc.get_service_info(service_type, name)
        if info:
            self._process_service(info, service_type)

    def remove_service(self, zc: Zeroconf, service_type: str, name: str):
        """Called when a service is removed"""
        logger.debug(f"Service removed: {name}")

    def _process_service(self, info, service_type: str):
        """Process discovered service"""
        try:
            from .discovery import DiscoveredDevice

            # Extract device information
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            ip_address = addresses[0] if addresses else None

            # Get properties
            properties = {}
            if info.properties:
                for key, value in info.properties.items():
                    try:
                        properties[key.decode('utf-8')] = value.decode('utf-8')
                    except:
                        pass

            # Create device
            device = DiscoveredDevice(
                device_id=f"mdns_{info.name}",
                device_type="unknown",  # Will be categorized
                name=info.name.split('.')[0],
                protocol="mdns",
                ip_address=ip_address,
                port=info.port,
                service_type=service_type,
                manufacturer=properties.get('manufacturer'),
                model=properties.get('model'),
                firmware_version=properties.get('version'),
                metadata=properties
            )

            # Call callback
            self.callback(device)

        except Exception as e:
            logger.error(f"Error processing mDNS service: {e}")


class MDNSDiscovery:
    """
    mDNS/Bonjour device discovery
    Discovers services on local network using multicast DNS
    """

    # Common mDNS service types
    SERVICE_TYPES = [
        "_http._tcp.local.",
        "_https._tcp.local.",
        "_hap._tcp.local.",        # HomeKit
        "_airplay._tcp.local.",    # AirPlay
        "_raop._tcp.local.",       # AirPlay audio
        "_homekit._tcp.local.",    # HomeKit
        "_hue._tcp.local.",        # Philips Hue
        "_googlecast._tcp.local.", # Chromecast
        "_spotify-connect._tcp.local.",  # Spotify
        "_sonos._tcp.local.",      # Sonos
        "_printer._tcp.local.",    # Printers
        "_ipp._tcp.local.",        # Internet Printing Protocol
        "_mqtt._tcp.local.",       # MQTT brokers
        "_coap._tcp.local.",       # CoAP
        "_workstation._tcp.local.",  # Computers
        "_ssh._tcp.local.",        # SSH servers
        "_sftp-ssh._tcp.local.",   # SFTP
        "_smb._tcp.local.",        # Samba/SMB
        "_afpovertcp._tcp.local.", # AFP (Apple File Protocol)
    ]

    def __init__(self):
        self.is_available = ZEROCONF_AVAILABLE
        self.zeroconf = None
        self.browsers = []
        self.scanning = False

    def start_scan(self, callback: Callable,
                   service_types: List[str] = None) -> Dict[str, Any]:
        """
        Start mDNS service discovery

        Args:
            callback: Callback function(device) for each discovery
            service_types: List of service types to discover
                          If None, uses default common services

        Returns:
            Dict with scan status
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "zeroconf not available. Install with: pip install zeroconf"
            }

        if self.scanning:
            return {
                "status": "error",
                "message": "Scan already in progress"
            }

        try:
            # Use default service types if not specified
            if service_types is None:
                service_types = self.SERVICE_TYPES

            # Create Zeroconf instance
            self.zeroconf = Zeroconf()

            # Create listener
            listener = MDNSServiceListener(callback)

            # Create browsers for each service type
            self.browsers = []
            for service_type in service_types:
                try:
                    browser = ServiceBrowser(self.zeroconf, service_type, listener)
                    self.browsers.append(browser)
                except Exception as e:
                    logger.warning(f"Error browsing {service_type}: {e}")

            self.scanning = True

            logger.info(f"mDNS scan started for {len(service_types)} service types")

            return {
                "status": "success",
                "message": "mDNS scan started",
                "service_types": len(service_types)
            }

        except Exception as e:
            logger.error(f"mDNS scan error: {e}")
            return {"status": "error", "message": str(e)}

    def stop_scan(self) -> Dict[str, Any]:
        """Stop mDNS discovery"""
        if not self.scanning:
            return {
                "status": "error",
                "message": "No scan in progress"
            }

        try:
            # Cancel browsers
            for browser in self.browsers:
                try:
                    browser.cancel()
                except:
                    pass

            # Close zeroconf
            if self.zeroconf:
                self.zeroconf.close()
                self.zeroconf = None

            self.browsers = []
            self.scanning = False

            logger.info("mDNS scan stopped")

            return {
                "status": "success",
                "message": "mDNS scan stopped"
            }

        except Exception as e:
            logger.error(f"mDNS stop error: {e}")
            return {"status": "error", "message": str(e)}

    def discover_service(self, service_type: str,
                        timeout: int = 5) -> Dict[str, Any]:
        """
        Discover specific service type

        Args:
            service_type: mDNS service type (e.g., "_http._tcp.local.")
            timeout: Discovery timeout in seconds

        Returns:
            Dict with discovered services
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "zeroconf not available"
            }

        discovered = []

        def on_discovery(device):
            discovered.append(device)

        # Start scan
        self.start_scan(on_discovery, service_types=[service_type])

        # Wait for timeout
        import time
        time.sleep(timeout)

        # Stop scan
        self.stop_scan()

        return {
            "status": "success",
            "service_type": service_type,
            "services": [d.to_dict() for d in discovered],
            "count": len(discovered)
        }

    def get_status(self) -> Dict[str, Any]:
        """Get scanner status"""
        return {
            "status": "success",
            "available": self.is_available,
            "scanning": self.scanning,
            "active_browsers": len(self.browsers)
        }
