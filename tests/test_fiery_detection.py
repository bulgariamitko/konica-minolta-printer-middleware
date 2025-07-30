#!/usr/bin/env python3
"""
Test script to detect and test Fiery controllers on C759 and C754e.
"""

import asyncio
import logging
from src.konika_middleware.devices.fiery_client import FieryClient
from src.konika_middleware.core.discovery import NetworkDiscovery
from src.konika_middleware.models.config import Settings


async def test_fiery_detection():
    """Test Fiery detection on your C759 and C754e machines."""
    print("🔥 TESTING FIERY CONTROLLER DETECTION")
    print("=" * 50)
    
    # Test your C759 and C754e machines
    fiery_machines = [
        ("192.168.1.210", "C759", "1234567812345678"),
        ("192.168.1.220", "C754e", "12345678")
    ]
    
    for ip, model, password in fiery_machines:
        print(f"\n🖨️  Testing {model} at {ip}")
        print("-" * 30)
        
        # Create Fiery client
        fiery_client = FieryClient(ip, password=password)
        
        # Test Fiery detection
        try:
            detection_result = await fiery_client.detect_fiery()
            
            print(f"Fiery Detected: {'✅ Yes' if detection_result['is_fiery'] else '❌ No'}")
            
            if detection_result['is_fiery']:
                print(f"Fiery Type: {detection_result.get('fiery_type', 'Unknown')}")
                print(f"Version: {detection_result.get('version', 'Unknown')}")
                print(f"Model: {detection_result.get('model', 'Unknown')}")
                print(f"Accessible Endpoints: {detection_result.get('accessible_endpoints', [])}")
                
                # Test authentication
                print("\n🔐 Testing Fiery Authentication...")
                auth_success = await fiery_client.authenticate()
                print(f"Authentication: {'✅ Success' if auth_success else '❌ Failed'}")
                
                # Test status
                print("\n📊 Testing Fiery Status...")
                status = await fiery_client.get_status()
                print(f"Status: {status.get('status', 'Unknown')}")
                print(f"Ready: {'✅ Yes' if status.get('ready') else '❌ No'}")
                print(f"Jobs Pending: {status.get('jobs_pending', 0)}")
                
                # Test capabilities
                print("\n⚙️  Testing Fiery Capabilities...")
                capabilities = await fiery_client.get_capabilities()
                print(f"Color Support: {'✅' if capabilities.get('supports_color') else '❌'}")
                print(f"Duplex Support: {'✅' if capabilities.get('supports_duplex') else '❌'}")
                print(f"RIP Processing: {'✅' if capabilities.get('rip_processing') else '❌'}")
                print(f"Supported Formats: {capabilities.get('supported_formats', [])}")
                
            else:
                print("❌ No Fiery controller detected")
                if detection_result.get('error'):
                    print(f"Error: {detection_result['error']}")
                    
        except Exception as e:
            print(f"❌ Fiery detection failed: {e}")


async def test_enhanced_discovery():
    """Test the enhanced discovery with Fiery support."""
    print("\n\n🔍 TESTING ENHANCED DISCOVERY WITH FIERY SUPPORT")
    print("=" * 60)
    
    settings = Settings()
    discovery = NetworkDiscovery(settings.snmp_community)
    
    # Test all your machines
    test_ips = ["192.168.1.200", "192.168.1.210", "192.168.1.220", "192.168.1.131"]
    
    print("Scanning all machines with enhanced Fiery detection...")
    discovered = await discovery.quick_scan(test_ips)
    
    print(f"\nFound {len(discovered)} KM devices:")
    
    for device_info in discovered:
        print(f"\n📱 {device_info['ip_address']}")
        print(f"   Model: {device_info.get('model', 'Unknown')}")
        print(f"   Device Type: {device_info.get('device_type', 'Unknown')}")
        print(f"   SNMP Accessible: {'✅' if device_info.get('snmp_info') else '❌'}")
        print(f"   HTTP Accessible: {'✅' if device_info.get('http_accessible') else '❌'}")
        print(f"   Fiery Controller: {'✅' if device_info.get('fiery_controller') else '❌'}")
        print(f"   Admin Password Found: {'✅' if device_info.get('admin_password') else '❌'}")
        
        if device_info.get('fiery_controller'):
            fiery_info = device_info.get('fiery_info', {})
            print(f"   Fiery Type: {fiery_info.get('fiery_type', 'Unknown')}")
            print(f"   Fiery Version: {fiery_info.get('version', 'Unknown')}")


async def test_device_manager_with_fiery():
    """Test device manager with Fiery support."""
    print("\n\n🔧 TESTING DEVICE MANAGER WITH FIERY SUPPORT")
    print("=" * 55)
    
    from src.konika_middleware.core.device_manager import DeviceManager
    from src.konika_middleware.models.config import Settings
    
    settings = Settings()
    device_manager = DeviceManager(settings)
    
    print("Starting device discovery with Fiery support...")
    devices = await device_manager.discover_devices()
    
    print(f"\nDevice manager found {len(devices)} devices:")
    
    for device in devices:
        print(f"\n🖨️  {device.name} ({device.id})")
        print(f"    IP: {device.ip_address}")
        print(f"    Type: {device.type}")
        print(f"    Password: {'✅' if device.admin_password else '❌'}")
        
        # Test device adapter
        try:
            adapter = await device_manager._get_device_adapter(device)
            print(f"    Adapter: {adapter.__class__.__name__}")
            
            # Test connection
            connection_test = await adapter.test_connection()
            print(f"    Connection Test: {'✅' if connection_test.get('status') == 'success' else '❌'}")
            
            if connection_test.get('fiery_detected'):
                print(f"    Fiery Detected: ✅")
                print(f"    Fiery Type: {connection_test.get('fiery_type', 'Unknown')}")
                print(f"    Controller Status: {connection_test.get('controller_status', 'Unknown')}")
            
        except Exception as e:
            print(f"    Adapter Error: {e}")


async def main():
    """Run all Fiery detection tests."""
    print("🔥 KONICA MINOLTA FIERY CONTROLLER TESTING")
    print("=" * 60)
    print("Testing Fiery controller detection for:")
    print("  • C759 (192.168.1.210) - Expected: Fiery controller")
    print("  • C754e (192.168.1.220) - Expected: Fiery controller")
    print("  • C654e (192.168.1.200) - Expected: Direct KM interface")
    print("  • KM2100 (192.168.1.131) - Expected: Direct KM interface")
    print()
    
    try:
        await test_fiery_detection()
        await test_enhanced_discovery()
        await test_device_manager_with_fiery()
        
        print("\n\n✅ FIERY TESTING COMPLETE!")
        print("If Fiery controllers were detected, your C759 and C754e should now work properly.")
        
    except Exception as e:
        print(f"\n❌ FIERY TESTING FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set up logging to see debug info
    logging.basicConfig(level=logging.INFO)
    
    # Run the tests
    asyncio.run(main())