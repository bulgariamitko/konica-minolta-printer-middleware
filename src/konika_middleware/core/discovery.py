"""Network discovery for Konica Minolta devices."""

import asyncio
import aiohttp
import ipaddress
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
import socket
import subprocess

from ..devices.snmp_client import SNMPClient
from ..models.device import Device, DeviceType


logger = logging.getLogger(__name__)


class NetworkDiscovery:
    """Discovers Konica Minolta devices on the network."""
    
    # Common admin passwords for different KM models
    COMMON_PASSWORDS = {
        "default": [
            "12345678",           # Most common default
            "1234567812345678",   # C654, C759
            "admin",              # Some models
            "",                   # No password
        ],
        "by_model": {
            "2100": ["12345678"],
            "754e": ["12345678"],
            "C654": ["1234567812345678"],
            "C759": ["1234567812345678"],
        }
    }
    
    # SNMP OIDs that identify Konica Minolta devices
    KM_IDENTIFIERS = [
        "KONICA MINOLTA",
        "bizhub",
        "magicolor",
        "pagepro"
    ]
    
    def __init__(self, snmp_community: str = "public"):
        self.snmp_community = snmp_community
        self.discovered_devices: List[Dict[str, Any]] = []
        
    async def discover_network_range(self, network: str = None) -> List[Dict[str, Any]]:
        """Discover KM devices in a network range."""
        if network is None:
            network = await self._get_local_network()
        
        logger.info(f"Starting device discovery on network: {network}")
        
        # Get all IPs in the range
        ip_range = list(ipaddress.IPv4Network(network, strict=False))
        
        # Scan for devices in parallel
        tasks = []
        semaphore = asyncio.Semaphore(50)  # Limit concurrent scans
        
        for ip in ip_range:
            if str(ip).endswith('.0') or str(ip).endswith('.255'):
                continue  # Skip network and broadcast addresses
            task = self._scan_device(str(ip), semaphore)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful discoveries
        devices = []
        for result in results:
            if isinstance(result, dict) and result.get('is_km_device'):
                devices.append(result)
        
        logger.info(f"Discovered {len(devices)} Konica Minolta devices")
        self.discovered_devices = devices
        return devices
    
    async def _get_local_network(self) -> str:
        """Get the local network range for scanning."""
        try:
            # Get default gateway
            result = await asyncio.create_subprocess_exec(
                'route', 'get', 'default',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await result.communicate()
            
            # Extract gateway IP
            gateway_match = re.search(r'gateway: (\d+\.\d+\.\d+\.\d+)', stdout.decode())
            if gateway_match:
                gateway = gateway_match.group(1)
                # Assume /24 network
                network_base = '.'.join(gateway.split('.')[:-1]) + '.0/24'
                return network_base
        except Exception:
            pass
        
        # Fallback to common network ranges
        return "192.168.0.0/24"
    
    async def _scan_device(self, ip: str, semaphore: asyncio.Semaphore) -> Optional[Dict[str, Any]]:
        """Scan a single IP for KM device."""
        async with semaphore:
            device_info = {
                'ip_address': ip,
                'is_km_device': False,
                'reachable': False,
                'device_type': None,
                'model': None,
                'snmp_info': {},
                'http_accessible': False,
                'admin_password': None,
                'capabilities': {}
            }
            
            try:
                # Quick ping check first
                if not await self._ping_host(ip):
                    return device_info
                
                device_info['reachable'] = True
                
                # Try SNMP discovery
                snmp_info = await self._snmp_discovery(ip)
                if snmp_info and self._is_konica_minolta(snmp_info):
                    device_info['is_km_device'] = True
                    device_info['snmp_info'] = snmp_info
                    device_info['model'] = self._extract_model(snmp_info)
                    device_info['device_type'] = self._determine_device_type(device_info['model'])
                
                # Try HTTP discovery
                http_info = await self._http_discovery(ip)
                if http_info:
                    device_info['http_accessible'] = True
                    if not device_info['is_km_device'] and self._is_konica_minolta(http_info):
                        device_info['is_km_device'] = True
                
                # If it's a KM device, try password discovery
                if device_info['is_km_device']:
                    password = await self._discover_admin_password(ip, device_info['model'])
                    device_info['admin_password'] = password
                    
                    # Get capabilities
                    capabilities = await self._get_device_capabilities(ip, device_info['model'], password)
                    device_info['capabilities'] = capabilities
                
                return device_info
                
            except Exception as e:
                logger.debug(f"Error scanning {ip}: {e}")
                return device_info
    
    async def _ping_host(self, ip: str) -> bool:
        """Quick ping test for host reachability."""
        try:
            process = await asyncio.create_subprocess_exec(
                'ping', '-c', '1', '-W', '1000', ip,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.communicate()
            return process.returncode == 0
        except Exception:
            return False
    
    async def _snmp_discovery(self, ip: str) -> Optional[Dict[str, Any]]:
        """Try SNMP discovery on device."""
        try:
            snmp_client = SNMPClient(ip, self.snmp_community)
            device_info = await snmp_client.get_device_info()
            return device_info
        except Exception:
            return None
    
    async def _http_discovery(self, ip: str) -> Optional[Dict[str, Any]]:
        """Try HTTP discovery on device."""
        try:
            timeout = aiohttp.ClientTimeout(total=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                
                # Try common web interface paths
                paths = ['/', '/wcd/', '/wcd/index.html']
                
                for path in paths:
                    try:
                        url = f"http://{ip}{path}"
                        async with session.get(url) as response:
                            if response.status in [200, 301, 302]:
                                content = await response.text()
                                return {
                                    'http_response': response.status,
                                    'content_snippet': content[:500],
                                    'headers': dict(response.headers)
                                }
                    except Exception:
                        continue
        except Exception:
            pass
        
        return None
    
    def _is_konica_minolta(self, info: Dict[str, Any]) -> bool:
        """Check if device info indicates a Konica Minolta device."""
        if not info:
            return False
        
        # Check SNMP description
        description = info.get('description', '').upper()
        for identifier in self.KM_IDENTIFIERS:
            if identifier.upper() in description:
                return True
        
        # Check HTTP content
        content = info.get('content_snippet', '').upper()
        for identifier in self.KM_IDENTIFIERS:
            if identifier.upper() in content:
                return True
        
        return False
    
    def _extract_model(self, info: Dict[str, Any]) -> Optional[str]:
        """Extract device model from discovery info."""
        description = info.get('description', '')
        
        # Common KM model patterns
        model_patterns = [
            r'bizhub\s+([C]?\d+[a-zA-Z]*)',
            r'magicolor\s+(\d+)',
            r'pagepro\s+(\d+)',
            r'AccurioPrint\s+(\d+)',
            r'KONICA MINOLTA\s+([C]?\d+[a-zA-Z]*)'
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _determine_device_type(self, model: Optional[str]) -> Optional[DeviceType]:
        """Determine DeviceType from model string."""
        if not model:
            return None
        
        model_upper = model.upper()
        
        if 'C654E' in model_upper:
            return DeviceType.C654E
        elif 'C759' in model_upper:
            return DeviceType.C759
        elif 'C754E' in model_upper:
            return DeviceType.C754E
        elif '2100' in model_upper:
            return DeviceType.KM2100
        
        # Default fallback based on model characteristics
        if model_upper.startswith('C') and any(x in model_upper for x in ['654', '754', '759']):
            return DeviceType.C654E  # Similar color models
        elif '2100' in model_upper:
            return DeviceType.KM2100
        
        return None
    
    async def _discover_admin_password(self, ip: str, model: Optional[str]) -> Optional[str]:
        """Try to discover admin password for the device."""
        passwords_to_try = []
        
        # Add model-specific passwords first
        if model:
            for model_key, passwords in self.COMMON_PASSWORDS["by_model"].items():
                if model_key.upper() in (model or "").upper():
                    passwords_to_try.extend(passwords)
        
        # Add default passwords
        passwords_to_try.extend(self.COMMON_PASSWORDS["default"])
        
        # Remove duplicates while preserving order
        passwords_to_try = list(dict.fromkeys(passwords_to_try))
        
        for password in passwords_to_try:
            try:
                if await self._test_admin_password(ip, password):
                    logger.info(f"Found admin password for {ip}: {'*' * len(password)}")
                    return password
            except Exception as e:
                logger.debug(f"Password test failed for {ip} with password '{'*' * len(password)}': {e}")
        
        return None
    
    async def _test_admin_password(self, ip: str, password: str) -> bool:
        """Test if an admin password works for a device."""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            
            # Set up session cookies (similar to our KM adapter)
            base_cookies = {
                'bv': 'Chrome/138.0.0.0',
                'uatype': 'NN',
                'lang': 'En',
                'favmode': 'false',
                'vm': 'Html',
                'param': '',
                'access': '',
                'bm': 'Low',
                'selno': 'En'
            }
            
            login_data = {
                'func': 'PSL_LP1_LOG',
                'password': password
            }
            
            async with aiohttp.ClientSession(
                cookies=base_cookies,
                timeout=timeout
            ) as session:
                
                url = f"http://{ip}/wcd/login.cgi"
                async with session.post(
                    url,
                    data=login_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                ) as response:
                    
                    # Success indicators: redirect, or 200 with admin cookies
                    if response.status in [200, 302]:
                        # Check for admin session cookies or redirect
                        cookies = dict(session.cookie_jar)
                        if any('ID' in str(cookie) for cookie in cookies) or response.status == 302:
                            return True
        
        except Exception:
            pass
        
        return False
    
    async def _get_device_capabilities(self, ip: str, model: Optional[str], password: Optional[str]) -> Dict[str, Any]:
        """Get device capabilities based on model and testing."""
        capabilities = {
            'supports_color': True,
            'supports_duplex': True,
            'max_paper_size': 'A4',
            'supported_formats': ['PDF', 'PS', 'PCL'],
            'authentication_required': password is not None,
            'admin_password_found': password is not None
        }
        
        # Model-specific capabilities
        if model:
            model_upper = model.upper()
            
            if any(x in model_upper for x in ['C654', 'C754', 'C759']):
                capabilities.update({
                    'supports_color': True,
                    'max_paper_size': 'A3',
                    'max_dpi': 1200,
                    'has_finisher': True,
                    'supported_formats': ['PDF', 'PS', 'PCL', 'XPS']
                })
            elif '2100' in model_upper:
                capabilities.update({
                    'supports_color': False,  # Monochrome
                    'max_paper_size': 'A4',
                    'max_dpi': 600,
                    'has_finisher': False
                })
        
        return capabilities
    
    def create_device_objects(self) -> List[Device]:
        """Convert discovered devices to Device objects."""
        devices = []
        
        for i, device_info in enumerate(self.discovered_devices):
            if not device_info.get('is_km_device'):
                continue
            
            # Generate device ID
            model = device_info.get('model') or 'unknown'
            # Handle None model safely
            model_safe = model if model and model != 'unknown' else 'unknown'
            device_id = f"km-{model_safe.lower()}-{device_info['ip_address'].replace('.', '-')}"
            
            # Create device name
            name = f"Konica Minolta {model}" if model and model != 'unknown' else f"Konica Minolta Device"
            
            # Create Device object
            device = Device(
                id=device_id,
                name=name,
                type=device_info.get('device_type') or DeviceType.C654E,
                ip_address=device_info['ip_address'],
                admin_password=device_info.get('admin_password'),
            )
            
            # Update capabilities if available
            if device_info.get('capabilities'):
                for key, value in device_info['capabilities'].items():
                    if hasattr(device.capabilities, key):
                        setattr(device.capabilities, key, value)
            
            devices.append(device)
        
        return devices
    
    async def quick_scan(self, ip_list: List[str]) -> List[Dict[str, Any]]:
        """Quick scan of specific IP addresses."""
        logger.info(f"Quick scanning {len(ip_list)} IP addresses")
        
        tasks = []
        semaphore = asyncio.Semaphore(20)
        
        for ip in ip_list:
            task = self._scan_device(ip, semaphore)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        devices = []
        for result in results:
            if isinstance(result, dict) and result.get('is_km_device'):
                devices.append(result)
        
        logger.info(f"Quick scan found {len(devices)} Konica Minolta devices")
        self.discovered_devices = devices
        return devices