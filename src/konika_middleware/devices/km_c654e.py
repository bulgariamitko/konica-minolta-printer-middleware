"""Konica Minolta C654e device adapter."""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import json

from .base_adapter import BaseDeviceAdapter
from .snmp_client import SNMPClient
from ..models.job import PrintJob
from ..core.exceptions import DeviceConnectionError, DeviceAuthenticationError


class KMC654eAdapter(BaseDeviceAdapter):
    """Adapter for Konica Minolta C654e printer."""
    
    def __init__(self, device, settings):
        super().__init__(device, settings)
        self.base_url = f"http://{device.ip_address}:{device.web_port}"
        self.wcd_url = f"{self.base_url}/wcd"
        self.session_cookies = {}
        self.authenticated = False
        self.snmp_client = SNMPClient(device.ip_address, settings.snmp_community)
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the C654e device."""
        results = {
            "device_type": "C654e",
            "tests": {}
        }
        
        # Test basic HTTP connectivity
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(self.base_url) as response:
                    results["tests"]["http_basic"] = {
                        "status": "pass" if response.status in [200, 301, 302] else "fail",
                        "status_code": response.status,
                        "message": f"HTTP response: {response.status}"
                    }
        except Exception as e:
            results["tests"]["http_basic"] = {
                "status": "error",
                "message": str(e)
            }
        
        # Test WCD interface
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.wcd_url}/index.html") as response:
                    results["tests"]["wcd_interface"] = {
                        "status": "pass" if response.status == 200 else "fail",
                        "status_code": response.status,
                        "message": f"WCD interface response: {response.status}"
                    }
        except Exception as e:
            results["tests"]["wcd_interface"] = {
                "status": "error",
                "message": str(e)
            }
        
        # Test SNMP
        try:
            device_info = await self.snmp_client.get_device_info()
            results["tests"]["snmp"] = {
                "status": "pass",
                "message": f"SNMP working: {device_info.get('description', 'Unknown device')}"
            }
        except Exception as e:
            results["tests"]["snmp"] = {
                "status": "fail",
                "message": str(e)
            }
        
        # Test authentication if password is configured
        if self.device.admin_password:
            try:
                auth_result = await self.authenticate()
                results["tests"]["authentication"] = {
                    "status": "pass" if auth_result else "fail",
                    "message": "Admin authentication successful" if auth_result else "Admin authentication failed"
                }
            except Exception as e:
                results["tests"]["authentication"] = {
                    "status": "error",
                    "message": str(e)
                }
        
        return results
    
    async def authenticate(self) -> bool:
        """Authenticate with the device using admin credentials."""
        if not self.device.admin_password:
            self.logger.warning("No admin password configured for authentication")
            return False
        
        try:
            # Set up session cookies
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
            
            # Prepare login data
            login_data = {
                'func': 'PSL_LP1_LOG',
                'password': self.device.admin_password
            }
            
            async with aiohttp.ClientSession(
                cookies=base_cookies,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                
                # Submit login
                async with session.post(
                    f"{self.wcd_url}/login.cgi",
                    data=login_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'}
                ) as response:
                    
                    if response.status == 200:
                        # Store session cookies - fix cookie handling
                        self.session_cookies = {}
                        for cookie in session.cookie_jar:
                            self.session_cookies[cookie.key] = cookie.value
                        self.authenticated = True
                        self.logger.info("Successfully authenticated with device")
                        return True
                    else:
                        self.logger.error(f"Authentication failed with status: {response.status}")
                        return False
        
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            raise DeviceAuthenticationError(f"Failed to authenticate with device: {str(e)}", self.device.id)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current device status."""
        status = {
            "device_id": self.device.id,
            "device_type": "C654e",
            "timestamp": asyncio.get_event_loop().time()
        }
        
        try:
            # Get basic connectivity status
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(self.base_url) as response:
                    status["http_status"] = response.status
                    status["reachable"] = response.status in [200, 301, 302]
        except Exception as e:
            status["http_status"] = None
            status["reachable"] = False
            status["error"] = str(e)
        
        # Get SNMP information
        try:
            device_info = await self.snmp_client.get_device_info()
            printer_status = await self.snmp_client.get_printer_status()
            supply_levels = await self.snmp_client.get_supply_levels()
            
            status.update({
                "snmp_info": device_info,
                "printer_status": printer_status.get("status", "unknown"),
                "pages_printed": printer_status.get("pages_printed"),
                "toner_levels": supply_levels
            })
        except Exception as e:
            status["snmp_error"] = str(e)
        
        # Get WCD-specific information if authenticated
        if self.authenticated and self.session_cookies:
            try:
                wcd_status = await self._get_wcd_status()
                status["wcd_status"] = wcd_status
            except Exception as e:
                status["wcd_error"] = str(e)
        
        return status
    
    async def _get_wcd_status(self) -> Dict[str, Any]:
        """Get status information through WCD interface."""
        try:
            async with aiohttp.ClientSession(
                cookies=self.session_cookies,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                
                # Try to get device information page
                async with session.get(f"{self.wcd_url}/version.html") as response:
                    if response.status == 200:
                        version_text = await response.text()
                        return {
                            "version_info": self._parse_version_info(version_text),
                            "authenticated": True
                        }
        
        except Exception as e:
            self.logger.error(f"WCD status error: {e}")
        
        return {"authenticated": False}
    
    def _parse_version_info(self, html_content: str) -> Dict[str, str]:
        """Parse version information from HTML content."""
        info = {}
        
        # Extract ROM version using simple string search
        if 'pcm_romversion' in html_content:
            start = html_content.find('pcm_romversion = "') + 19
            end = html_content.find('"', start)
            if start > 18 and end > start:
                info['rom_version'] = html_content[start:end]
        
        return info
    
    async def print_document(self, job: PrintJob) -> Dict[str, Any]:
        """Submit a print job to the device."""
        self._log_operation("print_document", job_id=job.id, title=job.title)
        
        try:
            # For C654e, we'll use IPP or direct printing since WCD doesn't have simple print API
            # This is a placeholder implementation
            
            # First, ensure we can connect to the device
            if not await self._check_device_ready():
                raise DeviceConnectionError("Device not ready for printing", self.device.id)
            
            # Try IPP printing first
            result = await self._print_via_ipp(job)
            if result.get("status") == "success":
                return result
            
            # Fall back to direct printing on port 9100
            result = await self._print_via_direct(job)
            return result
        
        except Exception as e:
            return self._handle_error("print_document", e)
    
    async def _check_device_ready(self) -> bool:
        """Check if device is ready to accept print jobs."""
        try:
            status = await self.get_status()
            return status.get("reachable", False) and status.get("printer_status") in ["idle", "ready"]
        except Exception:
            return False
    
    async def _print_via_ipp(self, job: PrintJob) -> Dict[str, Any]:
        """Attempt to print via IPP protocol."""
        # This is a placeholder - actual IPP implementation would require
        # proper IPP request formatting
        self.logger.info(f"IPP printing not fully implemented for job {job.id}")
        return {"status": "error", "message": "IPP printing not implemented"}
    
    async def _print_via_direct(self, job: PrintJob) -> Dict[str, Any]:
        """Attempt to print via direct connection to port 9100."""
        try:
            # Read the file to print
            with open(job.file_path, 'rb') as f:
                file_data = f.read()
            
            # Connect to printer's direct print port
            reader, writer = await asyncio.open_connection(
                self.device.ip_address, 
                self.device.direct_print_port
            )
            
            try:
                # For PDFs and other formats, we'd need to convert to PCL/PostScript
                # For now, just send raw data (works for plain text, PCL, PS)
                writer.write(file_data)
                await writer.drain()
                
                # Close connection
                writer.close()
                await writer.wait_closed()
                
                return {
                    "status": "success",
                    "message": f"Print job {job.id} sent to device",
                    "method": "direct_print",
                    "bytes_sent": len(file_data)
                }
            
            finally:
                if not writer.is_closing():
                    writer.close()
                    await writer.wait_closed()
        
        except Exception as e:
            return self._handle_error("direct_print", e)
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get device capabilities."""
        return {
            "supports_color": True,
            "supports_duplex": True,
            "max_paper_size": "A3",
            "supported_formats": ["PDF", "PS", "PCL", "TEXT"],
            "max_dpi": 1200,
            "print_methods": ["direct", "ipp"],
            "authentication_required": bool(self.device.admin_password),
            "has_finisher": False,
            "has_stapler": True,
            "has_hole_punch": True
        }