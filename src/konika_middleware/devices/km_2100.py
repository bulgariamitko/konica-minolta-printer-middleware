"""Konica Minolta 2100 device adapter."""

from .base_adapter import BaseDeviceAdapter
from .snmp_client import SNMPClient
from ..models.job import PrintJob


class KM2100Adapter(BaseDeviceAdapter):
    """Adapter for Konica Minolta 2100 printer.
    
    This is likely a monochrome device with different capabilities
    than the color models.
    """
    
    def __init__(self, device, settings):
        super().__init__(device, settings)
        self.base_url = f"http://{device.ip_address}:{device.web_port}"
        self.snmp_client = SNMPClient(device.ip_address, settings.snmp_community)
    
    async def test_connection(self) -> dict:
        """Test connection to the 2100 device."""
        results = {
            "device_type": "2100",
            "tests": {}
        }
        
        # Test SNMP (primary method for older devices)
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
        
        # Test direct printing port
        try:
            import asyncio
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self.device.ip_address, 9100),
                timeout=5.0
            )
            writer.close()
            await writer.wait_closed()
            
            results["tests"]["direct_print"] = {
                "status": "pass",
                "message": "Direct print port accessible"
            }
        except Exception as e:
            results["tests"]["direct_print"] = {
                "status": "fail",
                "message": str(e)
            }
        
        return results
    
    async def authenticate(self) -> bool:
        """Authentication for 2100 (may not be required)."""
        # Older devices often don't require authentication
        return True
    
    async def get_status(self) -> dict:
        """Get current device status."""
        status = {
            "device_id": self.device.id,
            "device_type": "2100",
            "reachable": False
        }
        
        try:
            device_info = await self.snmp_client.get_device_info()
            printer_status = await self.snmp_client.get_printer_status()
            
            status.update({
                "reachable": True,
                "snmp_info": device_info,
                "printer_status": printer_status.get("status", "unknown"),
                "pages_printed": printer_status.get("pages_printed")
            })
        except Exception as e:
            status["error"] = str(e)
        
        return status
    
    async def print_document(self, job: PrintJob) -> dict:
        """Submit a print job to the device."""
        import asyncio
        
        try:
            # Read the file to print
            with open(job.file_path, 'rb') as f:
                file_data = f.read()
            
            # Connect to printer's direct print port
            reader, writer = await asyncio.open_connection(
                self.device.ip_address, 
                9100
            )
            
            try:
                # Send raw data
                writer.write(file_data)
                await writer.drain()
                
                return {
                    "status": "success",
                    "message": f"Print job {job.id} sent to device",
                    "method": "direct_print",
                    "bytes_sent": len(file_data)
                }
            
            finally:
                writer.close()
                await writer.wait_closed()
        
        except Exception as e:
            return self._handle_error("print_document", e)
    
    async def get_capabilities(self) -> dict:
        """Get device capabilities."""
        return {
            "device_type": "2100",
            "supports_color": False,  # Monochrome device
            "supports_duplex": True,
            "max_paper_size": "A4",
            "supported_formats": ["PCL", "PS", "TEXT"],
            "max_dpi": 600,
            "print_methods": ["direct"],
            "authentication_required": False,
            "has_finisher": False,
            "has_stapler": False,
            "has_hole_punch": False
        }