#!/usr/bin/env python3
"""Test script to check device connectivity."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from konika_middleware.models.device import Device, DeviceType
from konika_middleware.models.config import Settings
from konika_middleware.devices.km_c654e import KMC654eAdapter


async def test_c654e_connection():
    """Test connection to KM C654e device."""
    print("Testing Konica Minolta C654e connection...")
    
    # Load settings
    settings = Settings()
    
    # Create device object
    device = Device(
        id="c654e-test",
        name="Test C654e",
        type=DeviceType.C654E,
        ip_address=settings.printer_c654e_ip,
        admin_password=settings.printer_c654e_password
    )
    
    # Create adapter
    adapter = KMC654eAdapter(device, settings)
    
    print(f"Testing device at {device.ip_address}...")
    
    # Test connection
    try:
        connection_result = await adapter.test_connection()
        print("\nConnection Test Results:")
        print("=" * 50)
        
        for test_name, result in connection_result.get("tests", {}).items():
            status_symbol = "✓" if result["status"] == "pass" else "✗" if result["status"] == "fail" else "⚠"
            print(f"{status_symbol} {test_name}: {result['message']}")
        
        # Test status
        print("\nGetting device status...")
        status = await adapter.get_status()
        print("Device Status:")
        print("-" * 30)
        print(f"Reachable: {status.get('reachable', False)}")
        print(f"HTTP Status: {status.get('http_status', 'N/A')}")
        print(f"Printer Status: {status.get('printer_status', 'Unknown')}")
        
        if 'snmp_info' in status:
            print(f"SNMP Description: {status['snmp_info'].get('description', 'N/A')}")
        
        if 'toner_levels' in status:
            print(f"Toner Levels: {status['toner_levels']}")
        
        # Test capabilities
        print("\nGetting device capabilities...")
        capabilities = await adapter.get_capabilities()
        print("Device Capabilities:")
        print("-" * 30)
        for key, value in capabilities.items():
            print(f"{key}: {value}")
        
        print("\n" + "=" * 50)
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("Konica Minolta Device Test")
    print("=" * 50)
    
    await test_c654e_connection()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)