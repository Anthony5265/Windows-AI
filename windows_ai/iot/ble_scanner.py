"""
Bluetooth LE Scanner
Discovers Bluetooth Low Energy devices
"""
from typing import Dict, Any, List, Callable, Optional
import logging
import threading
import time

logger = logging.getLogger(__name__)

try:
    from bleak import BleakScanner
    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False
    logger.warning("bleak not available. Install with: pip install bleak")


class BLEScanner:
    """
    Bluetooth Low Energy device scanner
    Discovers BLE devices (sensors, beacons, wearables, etc.)
    """

    def __init__(self):
        self.is_available = BLEAK_AVAILABLE
        self.scanning = False
        self.scan_task = None
        self.discovered_devices = {}

    def start_scan(self, callback: Callable,
                   duration: int = 10,
                   rssi_threshold: int = -80) -> Dict[str, Any]:
        """
        Start BLE device scan

        Args:
            callback: Callback function(device) for each discovery
            duration: Scan duration in seconds
            rssi_threshold: Minimum RSSI (signal strength) to report

        Returns:
            Dict with scan status
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "bleak not available. Install with: pip install bleak"
            }

        if self.scanning:
            return {
                "status": "error",
                "message": "Scan already in progress"
            }

        try:
            self.scanning = True
            self.discovered_devices.clear()

            # Start scan in background thread
            scan_thread = threading.Thread(
                target=self._scan_async,
                args=(callback, duration, rssi_threshold),
                daemon=True
            )
            scan_thread.start()

            logger.info(f"BLE scan started for {duration} seconds")

            return {
                "status": "success",
                "message": "BLE scan started",
                "duration": duration,
                "rssi_threshold": rssi_threshold
            }

        except Exception as e:
            logger.error(f"BLE scan error: {e}")
            self.scanning = False
            return {"status": "error", "message": str(e)}

    def stop_scan(self) -> Dict[str, Any]:
        """Stop BLE scan"""
        if not self.scanning:
            return {
                "status": "error",
                "message": "No scan in progress"
            }

        self.scanning = False

        logger.info("BLE scan stopped")

        return {
            "status": "success",
            "message": "BLE scan stopped",
            "discovered": len(self.discovered_devices)
        }

    def _scan_async(self, callback: Callable, duration: int, rssi_threshold: int):
        """Async BLE scan"""
        try:
            import asyncio

            # Create event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run scan
            loop.run_until_complete(
                self._do_scan(callback, duration, rssi_threshold)
            )

            loop.close()

        except Exception as e:
            logger.error(f"BLE scan error: {e}")
        finally:
            self.scanning = False

    async def _do_scan(self, callback: Callable, duration: int, rssi_threshold: int):
        """Perform BLE scan"""
        try:
            from .discovery import DiscoveredDevice

            def detection_callback(device, advertisement_data):
                """Called for each discovered device"""
                if not self.scanning:
                    return

                # Filter by RSSI
                rssi = advertisement_data.rssi
                if rssi < rssi_threshold:
                    return

                # Avoid duplicates
                if device.address in self.discovered_devices:
                    return

                # Extract device information
                manufacturer_data = advertisement_data.manufacturer_data
                manufacturer_id = None
                manufacturer_name = None

                if manufacturer_data:
                    # Get first manufacturer ID
                    manufacturer_id = list(manufacturer_data.keys())[0]
                    manufacturer_name = self._get_manufacturer_name(manufacturer_id)

                # Determine device type
                device_type = self._categorize_ble_device(
                    device.name,
                    advertisement_data.service_uuids
                )

                # Create discovered device
                discovered = DiscoveredDevice(
                    device_id=f"ble_{device.address.replace(':', '')}",
                    device_type=device_type,
                    name=device.name or f"BLE Device {device.address}",
                    protocol="ble",
                    mac_address=device.address,
                    manufacturer=manufacturer_name,
                    rssi=rssi,
                    metadata={
                        'rssi': rssi,
                        'manufacturer_id': manufacturer_id,
                        'service_uuids': advertisement_data.service_uuids,
                        'service_data': advertisement_data.service_data,
                        'local_name': advertisement_data.local_name,
                        'tx_power': advertisement_data.tx_power
                    }
                )

                # Store and callback
                self.discovered_devices[device.address] = discovered
                callback(discovered)

            # Start scan
            scanner = BleakScanner(detection_callback=detection_callback)
            await scanner.start()

            # Scan for duration
            start_time = time.time()
            while self.scanning and (time.time() - start_time) < duration:
                await asyncio.sleep(0.5)

            # Stop scan
            await scanner.stop()

        except Exception as e:
            logger.error(f"BLE scan error: {e}")

    def _categorize_ble_device(self, name: Optional[str],
                               service_uuids: List[str]) -> str:
        """Categorize BLE device based on name and services"""
        if name:
            name_lower = name.lower()

            # Fitness trackers / wearables
            if any(keyword in name_lower for keyword in ['fitbit', 'garmin', 'xiaomi', 'band', 'watch']):
                return 'wearable'

            # Sensors
            if any(keyword in name_lower for keyword in ['sensor', 'thermometer', 'hygrometer']):
                return 'sensor'

            # Beacons
            if 'beacon' in name_lower or 'ibeacon' in name_lower:
                return 'beacon'

            # Smart locks
            if 'lock' in name_lower or 'august' in name_lower:
                return 'lock'

            # Lights
            if 'light' in name_lower or 'bulb' in name_lower:
                return 'light'

        # Check service UUIDs
        if service_uuids:
            # Heart rate service
            if '0000180d-0000-1000-8000-00805f9b34fb' in service_uuids:
                return 'wearable'

            # Environmental sensing
            if '0000181a-0000-1000-8000-00805f9b34fb' in service_uuids:
                return 'sensor'

            # Battery service
            if '0000180f-0000-1000-8000-00805f9b34fb' in service_uuids:
                return 'peripheral'

        return 'unknown'

    def _get_manufacturer_name(self, manufacturer_id: int) -> Optional[str]:
        """Get manufacturer name from company ID"""
        # Common BLE manufacturer IDs
        manufacturers = {
            0x004C: "Apple",
            0x0006: "Microsoft",
            0x00E0: "Google",
            0x0075: "Samsung",
            0x0157: "Xiaomi",
            0x02E5: "Fitbit",
            0x018E: "Garmin",
            0x0087: "Polar",
            0x0131: "Philips",
            0x02DB: "Tile",
            0x0094: "Sony",
            0x000D: "Texas Instruments",
            0x000F: "Broadcom",
            0x001D: "Qualcomm",
            0x0059: "Nordic Semiconductor",
            0x006B: "ST Microelectronics",
        }

        return manufacturers.get(manufacturer_id)

    def discover_ble_devices(self, timeout: int = 10,
                             rssi_threshold: int = -80) -> Dict[str, Any]:
        """
        Discover BLE devices

        Args:
            timeout: Discovery timeout in seconds
            rssi_threshold: Minimum RSSI

        Returns:
            Dict with discovered devices
        """
        if not self.is_available:
            return {
                "status": "error",
                "message": "bleak not available"
            }

        discovered = []

        def on_discovery(device):
            discovered.append(device)

        # Start scan
        self.start_scan(on_discovery, duration=timeout, rssi_threshold=rssi_threshold)

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
