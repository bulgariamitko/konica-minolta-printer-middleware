#!/usr/bin/env python3
"""
Test script to demonstrate different device discovery modes.
This shows how AUTO_DISCOVER and MACHINE_LIST configurations work.
"""

import asyncio
import logging
from src.konika_middleware.models.config import Settings
from src.konika_middleware.core.device_manager import DeviceManager


async def test_predefined_mode():
    """Test predefined machine list mode (AUTO_DISCOVER=false)."""
    print("🔧 TESTING PREDEFINED MACHINE LIST MODE")
    print("="*60)
    
    # Create settings with predefined machines
    settings = Settings(
        auto_discover=False,
        machine_list="192.168.0.100:password123,192.168.0.101:,192.168.0.102:",
        snmp_community="public"
    )
    
    print(f"AUTO_DISCOVER: {settings.auto_discover}")
    print(f"MACHINE_LIST: {settings.machine_list}")
    
    # Parse the machine list
    machines = settings.parse_machine_list()
    print(f"Parsed machines: {machines}")
    print()
    
    # Create device manager
    device_manager = DeviceManager(settings)
    
    # Test device discovery (will use predefined list)
    print("Starting device discovery...")
    devices = await device_manager.discover_devices()
    
    print(f"Found {len(devices)} devices:")
    for device in devices:
        print(f"  - {device.name} ({device.id}) at {device.ip_address}")
        if device.admin_password:
            print(f"    Password: {'*' * len(device.admin_password)}")
    print()


async def test_auto_discover_mode():
    """Test automatic discovery mode (AUTO_DISCOVER=true)."""
    print("🔍 TESTING AUTO-DISCOVERY MODE")
    print("="*60)
    
    # Create settings with auto-discovery
    settings = Settings(
        auto_discover=True,
        discovery_network="192.168.0.0/24",
        snmp_community="public"
    )
    
    print(f"AUTO_DISCOVER: {settings.auto_discover}")
    print(f"DISCOVERY_NETWORK: {settings.discovery_network}")
    print()
    
    # Create device manager
    device_manager = DeviceManager(settings)
    
    # Test device discovery (will scan network)
    print("Starting network discovery (this may take a while)...")
    print("NOTE: This will scan the entire network range for KM devices")
    
    # For demo purposes, we'll just show how it would work
    print("⚠️  Network scanning disabled in demo - would scan:", settings.discovery_network)
    print("   In real usage, this would automatically find all KM printers on the network")
    print()


async def test_legacy_mode():
    """Test legacy individual printer settings."""
    print("🗄️  TESTING LEGACY INDIVIDUAL PRINTER MODE")
    print("="*60)
    
    # Create settings with legacy individual settings
    settings = Settings(
        auto_discover=False,
        machine_list="",  # Empty list triggers legacy mode
        printer_c654e_ip="192.168.0.100",
        printer_c654e_password="password123",
        printer_c759_ip="192.168.0.101",
        snmp_community="public"
    )
    
    print("MACHINE_LIST: (empty - using legacy settings)")
    print(f"PRINTER_C654E_IP: {settings.printer_c654e_ip}")
    print(f"PRINTER_C654E_PASSWORD: {'*' * len(settings.printer_c654e_password) if settings.printer_c654e_password else '(none)'}")
    print(f"PRINTER_C759_IP: {settings.printer_c759_ip}")
    
    # Parse the machine list (should fallback to legacy)
    machines = settings.parse_machine_list()
    print(f"Parsed machines (from legacy settings): {machines}")
    print()


async def main():
    """Run all configuration mode tests."""
    print("🖨️  KONICA MINOLTA MIDDLEWARE - CONFIGURATION MODE TESTING")
    print("="*70)
    print("This demonstrates the different ways to configure device discovery:")
    print("1. Predefined machine list (MACHINE_LIST)")
    print("2. Automatic network discovery (AUTO_DISCOVER=true)")
    print("3. Legacy individual printer settings")
    print()
    
    try:
        await test_predefined_mode()
        await test_auto_discover_mode()
        await test_legacy_mode()
        
        print("✅ CONFIGURATION TESTING COMPLETE")
        print()
        print("📝 CONFIGURATION SUMMARY:")
        print("  • Set AUTO_DISCOVER=false and use MACHINE_LIST for specific printers")
        print("  • Set AUTO_DISCOVER=true for automatic network scanning")
        print("  • Legacy individual settings still supported for backwards compatibility")
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set up basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the tests
    asyncio.run(main())