"""SNMP client for device monitoring."""

import asyncio
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SNMPClient:
    """SNMP client for querying device information."""
    
    # Common SNMP OIDs for printers
    SYSTEM_OID = "1.3.6.1.2.1.1"
    PRINTER_OID = "1.3.6.1.2.1.43"
    
    # Specific OIDs
    SYSTEM_DESCRIPTION = "1.3.6.1.2.1.1.1.0"
    SYSTEM_UPTIME = "1.3.6.1.2.1.1.3.0"
    SYSTEM_NAME = "1.3.6.1.2.1.1.5.0"
    
    # Printer-specific OIDs
    PRINTER_STATUS = "1.3.6.1.2.1.25.3.2.1.5.1"
    PRINTER_PAGES_PRINTED = "1.3.6.1.2.1.43.10.2.1.4.1.1"
    
    def __init__(self, host: str, community: str = "public", version: str = "2c", timeout: int = 5):
        self.host = host
        self.community = community
        self.version = version
        self.timeout = timeout
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get basic device information via SNMP."""
        try:
            # Use subprocess to call snmpget/snmpwalk since pysnmp is complex for async
            result = await self._run_snmp_command("snmpwalk", [
                "-v", self.version,
                "-c", self.community,
                self.host,
                self.SYSTEM_OID
            ])
            
            return self._parse_system_info(result)
            
        except Exception as e:
            logger.error(f"SNMP query failed for {self.host}: {e}")
            raise
    
    async def get_printer_status(self) -> Dict[str, Any]:
        """Get printer-specific status information."""
        try:
            # Get printer status
            status_result = await self._run_snmp_command("snmpget", [
                "-v", self.version,
                "-c", self.community,
                self.host,
                self.PRINTER_STATUS
            ])
            
            # Get pages printed (if available)
            pages_result = await self._run_snmp_command("snmpget", [
                "-v", self.version,
                "-c", self.community,
                self.host,
                self.PRINTER_PAGES_PRINTED
            ])
            
            return {
                "status": self._parse_printer_status(status_result),
                "pages_printed": self._parse_pages_printed(pages_result)
            }
            
        except Exception as e:
            logger.error(f"SNMP printer status query failed for {self.host}: {e}")
            return {"status": "unknown", "pages_printed": None}
    
    async def get_supply_levels(self) -> Dict[str, Any]:
        """Get toner/supply level information."""
        try:
            # Query supply levels (OID varies by manufacturer)
            result = await self._run_snmp_command("snmpwalk", [
                "-v", self.version,
                "-c", self.community,
                self.host,
                "1.3.6.1.2.1.43.11.1.1"  # Supply levels
            ])
            
            return self._parse_supply_levels(result)
            
        except Exception as e:
            logger.error(f"SNMP supply levels query failed for {self.host}: {e}")
            return {}
    
    async def _run_snmp_command(self, command: str, args: list) -> str:
        """Run SNMP command and return output."""
        cmd = [command] + args
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            raise Exception(f"SNMP command failed: {stderr.decode()}")
        
        return stdout.decode()
    
    def _parse_system_info(self, snmp_output: str) -> Dict[str, Any]:
        """Parse system information from SNMP output."""
        info = {}
        
        for line in snmp_output.strip().split('\n'):
            if '::sysDescr.0' in line:
                info['description'] = line.split('= STRING: ', 1)[-1]
            elif '::sysUpTimeInstance' in line:
                info['uptime'] = line.split('= Timeticks: ', 1)[-1]
            elif '::sysName.0' in line:
                info['name'] = line.split('= STRING: ', 1)[-1]
        
        return info
    
    def _parse_printer_status(self, snmp_output: str) -> str:
        """Parse printer status from SNMP output."""
        # This is a simplified parser - actual implementation would need
        # to handle different status codes properly
        if "1" in snmp_output:
            return "idle"
        elif "3" in snmp_output:
            return "printing"
        elif "4" in snmp_output:
            return "warmup"
        else:
            return "unknown"
    
    def _parse_pages_printed(self, snmp_output: str) -> Optional[int]:
        """Parse pages printed counter from SNMP output."""
        try:
            # Extract number from SNMP output
            for line in snmp_output.strip().split('\n'):
                if 'Counter32:' in line:
                    return int(line.split('Counter32: ')[-1])
        except (ValueError, IndexError):
            pass
        return None
    
    def _parse_supply_levels(self, snmp_output: str) -> Dict[str, int]:
        """Parse supply levels from SNMP output."""
        supplies = {}
        
        # This is a simplified parser - actual implementation would need
        # more sophisticated parsing based on the device's MIB
        lines = snmp_output.strip().split('\n')
        
        for i, line in enumerate(lines):
            if 'Supply' in line or 'Toner' in line:
                try:
                    # Try to find a percentage value in subsequent lines
                    for j in range(i, min(i+5, len(lines))):
                        if 'INTEGER:' in lines[j]:
                            level = int(lines[j].split('INTEGER: ')[-1])
                            if 0 <= level <= 100:
                                color = 'black'  # Default
                                if 'cyan' in line.lower():
                                    color = 'cyan'
                                elif 'magenta' in line.lower():
                                    color = 'magenta'
                                elif 'yellow' in line.lower():
                                    color = 'yellow'
                                
                                supplies[color] = level
                                break
                except (ValueError, IndexError):
                    continue
        
        return supplies