"""Device management and coordination."""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from ..models.device import Device, DeviceStatus, DeviceType, DeviceStatusResponse
from ..models.config import Settings
from .exceptions import DeviceNotFoundError, DeviceConnectionError
from .discovery import NetworkDiscovery


logger = logging.getLogger(__name__)


class DeviceManager:
    """Manages all printer devices and their status."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._devices: Dict[str, Device] = {}
        self._device_adapters: Dict[str, any] = {}  # Will hold device-specific adapters
        self._status_check_interval = 30  # seconds
        self._status_check_task: Optional[asyncio.Task] = None
        self._discovery = NetworkDiscovery(settings.snmp_community)
        
        # Initialize devices (now empty, will be populated by discovery)
        self._initialize_devices()
    
    def _initialize_devices(self) -> None:
        """Initialize devices - will be populated by discovery."""
        # Start with empty device list - devices will be added via discovery
        logger.info("Device manager initialized - devices will be discovered dynamically")
    
    async def start(self) -> None:
        """Start the device manager and status monitoring."""
        logger.info("Starting device manager...")
        
        # Start periodic status checks
        self._status_check_task = asyncio.create_task(self._periodic_status_check())
        
        # Initial device discovery
        await self.discover_devices()
        
        # Initial status check
        await self.refresh_all_devices()
    
    async def stop(self) -> None:
        """Stop the device manager."""
        logger.info("Stopping device manager...")
        
        if self._status_check_task:
            self._status_check_task.cancel()
            try:
                await self._status_check_task
            except asyncio.CancelledError:
                pass
    
    async def _periodic_status_check(self) -> None:
        """Periodically check status of all devices."""
        while True:
            try:
                await asyncio.sleep(self._status_check_interval)
                await self.refresh_all_devices()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during periodic status check: {e}")
    
    def get_device(self, device_id: str) -> Device:
        """Get a device by ID."""
        if device_id not in self._devices:
            raise DeviceNotFoundError(device_id)
        return self._devices[device_id]
    
    def list_devices(self) -> List[Device]:
        """Get list of all devices."""
        return list(self._devices.values())
    
    def get_online_devices(self) -> List[Device]:
        """Get list of online devices."""
        return [device for device in self._devices.values() 
                if device.status == DeviceStatus.ONLINE]
    
    def get_available_devices(self) -> List[Device]:
        """Get list of devices available for printing (online and not busy)."""
        return [device for device in self._devices.values() 
                if device.status in [DeviceStatus.ONLINE]]
    
    async def refresh_all_devices(self) -> None:
        """Refresh status of all devices."""
        tasks = [self.refresh_device_status(device_id) 
                for device_id in self._devices.keys()]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def refresh_device_status(self, device_id: str) -> DeviceStatusResponse:
        """Refresh and return status of a specific device."""
        device = self.get_device(device_id)
        
        try:
            # Get device adapter (will implement this next)
            adapter = await self._get_device_adapter(device)
            
            # Check connectivity
            is_online = await self._check_device_connectivity(device)
            
            if is_online:
                # Get detailed status from device
                status_info = await adapter.get_status()
                
                # Update device status
                device.status = DeviceStatus.ONLINE
                device.last_seen = datetime.utcnow()
                device.error_message = None
                
                # Update device information
                if hasattr(status_info, 'toner_levels'):
                    device.toner_levels = status_info.toner_levels
                if hasattr(status_info, 'paper_levels'):
                    device.paper_levels = status_info.paper_levels
                
                logger.debug(f"Device {device_id} is online")
                
            else:
                device.status = DeviceStatus.OFFLINE
                device.error_message = "Device not reachable"
                logger.warning(f"Device {device_id} is offline")
        
        except Exception as e:
            device.status = DeviceStatus.ERROR
            device.error_message = str(e)
            logger.error(f"Error checking device {device_id}: {e}")
        
        # Create status response
        return DeviceStatusResponse(
            device_id=device_id,
            status=device.status,
            last_updated=datetime.utcnow(),
            toner_levels=device.toner_levels,
            paper_levels=device.paper_levels,
            has_errors=device.status == DeviceStatus.ERROR,
            error_messages=[device.error_message] if device.error_message else []
        )
    
    async def _check_device_connectivity(self, device: Device) -> bool:
        """Check basic connectivity to a device."""
        import aiohttp
        
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"http://{device.ip_address}:{device.web_port}"
                async with session.get(url) as response:
                    return response.status in [200, 301, 302, 401]  # Accept redirects and auth required
        except Exception:
            return False
    
    async def _get_device_adapter(self, device: Device):
        """Get or create device adapter for specific device type."""
        if device.id not in self._device_adapters:
            # Import and create adapter based on device type
            if device.type == DeviceType.C654E:
                from ..devices.km_c654e import KMC654eAdapter
                adapter = KMC654eAdapter(device, self.settings)
            elif device.type == DeviceType.C759:
                from ..devices.km_c759 import KMC759Adapter  # We'll create this
                adapter = KMC759Adapter(device, self.settings)
            elif device.type == DeviceType.C754E:
                from ..devices.km_c754e import KMC754eAdapter  # We'll create this
                adapter = KMC754eAdapter(device, self.settings)
            elif device.type == DeviceType.KM2100:
                from ..devices.km_2100 import KM2100Adapter  # We'll create this
                adapter = KM2100Adapter(device, self.settings)
            else:
                raise ValueError(f"Unsupported device type: {device.type}")
            
            self._device_adapters[device.id] = adapter
        
        return self._device_adapters[device.id]
    
    async def test_device_connection(self, device_id: str) -> Dict[str, any]:
        """Test connection to a specific device and return detailed results."""
        device = self.get_device(device_id)
        
        result = {
            "device_id": device_id,
            "device_name": device.name,
            "ip_address": device.ip_address,
            "tests": {}
        }
        
        # Test basic HTTP connectivity
        try:
            is_reachable = await self._check_device_connectivity(device)
            result["tests"]["http_connectivity"] = {
                "status": "pass" if is_reachable else "fail",
                "message": "Device is reachable via HTTP" if is_reachable else "Device not reachable"
            }
        except Exception as e:
            result["tests"]["http_connectivity"] = {
                "status": "error",
                "message": str(e)
            }
        
        # Test SNMP connectivity
        try:
            from ..devices.snmp_client import SNMPClient
            snmp = SNMPClient(device.ip_address, self.settings.snmp_community)
            device_info = await snmp.get_device_info()
            result["tests"]["snmp_connectivity"] = {
                "status": "pass",
                "message": f"SNMP working, device: {device_info.get('description', 'Unknown')}"
            }
        except Exception as e:
            result["tests"]["snmp_connectivity"] = {
                "status": "fail",
                "message": str(e)
            }
        
        # Test device-specific features
        try:
            adapter = await self._get_device_adapter(device)
            adapter_test = await adapter.test_connection()
            result["tests"]["device_adapter"] = adapter_test
        except Exception as e:
            result["tests"]["device_adapter"] = {
                "status": "error",
                "message": str(e)
            }
        
        return result
    
    def get_device_statistics(self) -> Dict[str, any]:
        """Get statistics about all devices."""
        total_devices = len(self._devices)
        online_count = len([d for d in self._devices.values() if d.status == DeviceStatus.ONLINE])
        offline_count = len([d for d in self._devices.values() if d.status == DeviceStatus.OFFLINE])
        error_count = len([d for d in self._devices.values() if d.status == DeviceStatus.ERROR])
        busy_count = len([d for d in self._devices.values() if d.status == DeviceStatus.BUSY])
        
        return {
            "total_devices": total_devices,
            "online_count": online_count,
            "offline_count": offline_count,
            "error_count": error_count,
            "busy_count": busy_count,
            "availability_percent": (online_count / total_devices * 100) if total_devices > 0 else 0
        }
    
    async def discover_devices(self, network: str = None) -> List[Device]:
        """Discover Konica Minolta devices based on configuration."""
        if self.settings.auto_discover:
            logger.info("Starting automatic network device discovery...")
            return await self._auto_discover_devices(network)
        else:
            logger.info("Using predefined machine list...")
            return await self._load_predefined_devices()
    
    async def _auto_discover_devices(self, network: str = None) -> List[Device]:
        """Perform automatic network discovery."""
        try:
            # Use configured network or provided network
            discovery_network = network or self.settings.discovery_network
            
            # Perform network discovery
            discovered_info = await self._discovery.discover_network_range(discovery_network)
            
            # Convert to Device objects
            new_devices = self._discovery.create_device_objects()
            
            # Add discovered devices to our managed devices
            added_count = 0
            for device in new_devices:
                if device.id not in self._devices:
                    self._devices[device.id] = device
                    added_count += 1
                    logger.info(f"Added discovered device: {device.name} ({device.id}) at {device.ip_address}")
                else:
                    # Update existing device with new information
                    existing = self._devices[device.id]
                    if device.admin_password and not existing.admin_password:
                        existing.admin_password = device.admin_password
                        logger.info(f"Updated admin password for device: {device.id}")
            
            logger.info(f"Auto-discovery complete: {added_count} new devices added, {len(new_devices)} total discovered")
            return new_devices
        
        except Exception as e:
            logger.error(f"Auto-discovery failed: {e}")
            return []
    
    async def _load_predefined_devices(self) -> List[Device]:
        """Load devices from predefined machine list."""
        try:
            machine_list = self.settings.parse_machine_list()
            
            if not machine_list:
                logger.warning("No machines defined in MACHINE_LIST or legacy settings")
                return []
            
            # Extract IPs for discovery
            ip_list = [ip for ip, _ in machine_list]
            logger.info(f"Loading predefined devices: {ip_list}")
            
            # Perform quick scan of specific IPs
            discovered_info = await self._discovery.quick_scan(ip_list)
            
            # Convert to Device objects
            new_devices = self._discovery.create_device_objects()
            
            # Override passwords from configuration
            for device in new_devices:
                for ip, password in machine_list:
                    if device.ip_address == ip and password:
                        device.admin_password = password
                        logger.info(f"Applied configured password for device at {ip}")
            
            # Add to managed devices
            added_count = 0
            for device in new_devices:
                if device.id not in self._devices:
                    self._devices[device.id] = device
                    added_count += 1
                    logger.info(f"Added predefined device: {device.name} ({device.id}) at {device.ip_address}")
                else:
                    # Update existing device
                    existing = self._devices[device.id]
                    if device.admin_password and not existing.admin_password:
                        existing.admin_password = device.admin_password
                        logger.info(f"Updated admin password for device: {device.id}")
            
            logger.info(f"Predefined device loading complete: {added_count} new devices added")
            return new_devices
        
        except Exception as e:
            logger.error(f"Predefined device loading failed: {e}")
            return []
    
    async def discover_specific_ips(self, ip_list: List[str]) -> List[Device]:
        """Discover devices at specific IP addresses."""
        logger.info(f"Discovering devices at specific IPs: {ip_list}")
        
        try:
            # Perform quick scan
            discovered_info = await self._discovery.quick_scan(ip_list)
            
            # Convert to Device objects
            new_devices = self._discovery.create_device_objects()
            
            # Add to managed devices
            added_count = 0
            for device in new_devices:
                if device.id not in self._devices:
                    self._devices[device.id] = device
                    added_count += 1
                    logger.info(f"Added device: {device.name} ({device.id}) at {device.ip_address}")
            
            logger.info(f"Specific IP discovery complete: {added_count} new devices added")
            return new_devices
        
        except Exception as e:
            logger.error(f"Specific IP discovery failed: {e}")
            return []
    
    def add_device_manually(self, device: Device) -> None:
        """Manually add a device to the manager."""
        self._devices[device.id] = device
        logger.info(f"Manually added device: {device.name} ({device.id}) at {device.ip_address}")
    
    def remove_device(self, device_id: str) -> bool:
        """Remove a device from the manager."""
        if device_id in self._devices:
            device = self._devices.pop(device_id)
            if device_id in self._device_adapters:
                self._device_adapters.pop(device_id)
            logger.info(f"Removed device: {device.name} ({device_id})")
            return True
        return False
    
    def get_discovery_info(self) -> List[Dict[str, any]]:
        """Get raw discovery information from last scan."""
        return self._discovery.discovered_devices