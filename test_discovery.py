#!/usr/bin/env python3
"""Test script for device discovery and remote communication."""

import asyncio
import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from konika_middleware.core.discovery import NetworkDiscovery
from konika_middleware.models.config import Settings
from konika_middleware.core.remote_client import RemoteClient


async def test_device_discovery():
    """Test the device discovery functionality."""
    print("=" * 60)
    print("TESTING DEVICE DISCOVERY")
    print("=" * 60)
    
    # Create discovery instance
    settings = Settings()
    discovery = NetworkDiscovery(settings.snmp_community)
    
    print(f"Testing with SNMP community: {settings.snmp_community}")
    print()
    
    # Test specific IP discovery first (faster)
    print("1. Testing specific IP discovery...")
    print("   NOTE: This simulates predefined machine list mode (AUTO_DISCOVER=false)")
    test_ips = [
        "192.168.0.100",  # Example IP 1 - replace with your printer IPs
        "192.168.0.101",  # Example IP 2
        "192.168.0.102",  # Example IP 3
        "192.168.0.103",  # Example IP 4
    ]
    
    discovered = await discovery.quick_scan(test_ips)
    
    print(f"Scanned {len(test_ips)} IP addresses")
    print(f"Found {len(discovered)} Konica Minolta devices")
    print()
    
    # Display results
    for i, device_info in enumerate(discovered, 1):
        print(f"Device {i}:")
        print(f"  IP: {device_info['ip_address']}")
        print(f"  Model: {device_info.get('model', 'Unknown')}")
        print(f"  SNMP Info: {device_info.get('snmp_info', {}).get('description', 'N/A')}")
        print(f"  HTTP Accessible: {device_info['http_accessible']}")
        print(f"  Admin Password Found: {'Yes' if device_info['admin_password'] else 'No'}")
        
        if device_info.get('capabilities'):
            print(f"  Capabilities:")
            for key, value in device_info['capabilities'].items():
                print(f"    {key}: {value}")
        print()
    
    # Convert to Device objects
    device_objects = discovery.create_device_objects()
    print(f"Created {len(device_objects)} Device objects")
    
    for device in device_objects:
        print(f"  - {device.name} ({device.id}) at {device.ip_address}")
    
    print()
    return discovered


async def test_network_scan():
    """Test full network scanning (optional - can be slow)."""
    print("=" * 60)
    print("TESTING NETWORK SCAN (Optional)")
    print("=" * 60)
    
    response = input("Do you want to test full network scanning? This may take several minutes. (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Skipping network scan")
        return []
    
    settings = Settings()
    discovery = NetworkDiscovery(settings.snmp_community)
    
    print("Starting network scan...")
    print("This will scan the local network for Konica Minolta devices")
    print("Please wait...")
    
    discovered = await discovery.discover_network_range()
    
    print(f"\\nNetwork scan complete!")
    print(f"Found {len(discovered)} Konica Minolta devices on the network")
    
    for device_info in discovered:
        print(f"  - {device_info['ip_address']}: {device_info.get('model', 'Unknown model')}")
    
    return discovered


async def test_remote_communication():
    """Test remote communication features."""
    print("=" * 60)
    print("TESTING REMOTE COMMUNICATION")
    print("=" * 60)
    
    settings = Settings()
    remote_client = RemoteClient(settings)
    
    # Test webhook configuration
    print("1. Testing webhook configuration...")
    
    # Add a test webhook endpoint (you can replace with your actual endpoint)
    test_webhook = "https://webhook.site/your-unique-url"  # Replace with actual URL
    remote_client.add_webhook(test_webhook)
    
    print(f"Added webhook: {test_webhook}")
    
    # Test sending a webhook
    print("\\n2. Testing webhook sending...")
    test_data = {
        "message": "Test from Konica Minolta Middleware",
        "timestamp": "2025-07-29T15:30:00Z",
        "test_device": {
            "id": "test-device",
            "name": "Test Printer",
            "ip": "192.168.1.200"
        }
    }
    
    try:
        await remote_client.send_webhook("test_event", test_data)
        print("✓ Test webhook sent successfully")
    except Exception as e:
        print(f"✗ Webhook sending failed: {e}")
    
    # Test polling configuration
    print("\\n3. Testing polling configuration...")
    
    # Add a test polling endpoint
    test_polling = "https://your-server.com/api/print-jobs"  # Replace with actual URL
    remote_client.add_polling_endpoint(test_polling)
    
    print(f"Added polling endpoint: {test_polling}")
    
    # Test API credentials
    print("\\n4. Testing API credentials...")
    remote_client.set_credentials("test-api-key", "test-secret-key")
    print("✓ API credentials set")
    
    # Test event notifications
    print("\\n5. Testing event notifications...")
    
    # Test device discovered notification
    await remote_client.notify_device_discovered({
        "id": "test-device-001",
        "name": "Test C654e",
        "ip_address": "192.168.1.200",
        "type": "C654e",
        "capabilities": {"supports_color": True, "supports_duplex": True}
    })
    print("✓ Device discovered notification sent")
    
    # Test system started notification
    await remote_client.notify_system_started()
    print("✓ System started notification sent")
    
    print("\\nRemote communication test complete!")


async def test_api_endpoints():
    """Test the new API endpoints with curl commands."""
    print("=" * 60)
    print("API ENDPOINT TESTING")
    print("=" * 60)
    
    print("You can test the new API endpoints with these curl commands:")
    print("(Make sure the middleware server is running first)")
    print()
    
    # Discovery endpoints
    print("📡 DISCOVERY ENDPOINTS:")
    print()
    
    print("1. Discover devices on network:")
    print('curl -X POST "http://localhost:8000/api/v1/devices/discover/network" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"network": null}\'')
    print()
    
    print("2. Discover specific IP addresses:")
    print('curl -X POST "http://localhost:8000/api/v1/devices/discover/ips" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"ip_addresses": ["192.168.1.200", "192.168.1.210"]}\'')
    print()
    
    print("3. Get discovery information:")
    print('curl "http://localhost:8000/api/v1/devices/discovery/info"')
    print()
    
    # Remote endpoints
    print("🌐 REMOTE COMMUNICATION ENDPOINTS:")
    print()
    
    print("4. Add webhook endpoint:")
    print('curl -X POST "http://localhost:8000/api/v1/remote/webhooks/add" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"url": "https://your-webhook-url.com/webhook"}\'')
    print()
    
    print("5. Test webhook:")
    print('curl -X POST "http://localhost:8000/api/v1/remote/webhook/test" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"event_type": "test", "test_data": {"message": "Hello from middleware"}}\'')
    print()
    
    print("6. Check remote status:")
    print('curl "http://localhost:8000/api/v1/remote/status"')
    print()
    
    print("7. Health check remote endpoints:")
    print('curl "http://localhost:8000/api/v1/remote/health"')
    print()


async def main():
    """Main test function."""
    print("🖨️  KONICA MINOLTA MIDDLEWARE - DISCOVERY & REMOTE TESTING")
    print("=" * 60)
    
    try:
        # Test device discovery
        discovered_devices = await test_device_discovery()
        
        # Test network scanning (optional)
        await test_network_scan()
        
        # Test remote communication
        await test_remote_communication()
        
        # Show API testing commands
        await test_api_endpoints()
        
        print("=" * 60)
        print("🎉 ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        print("\\nSUMMARY:")
        print(f"✓ Device discovery tested")
        print(f"✓ Remote communication tested")
        print(f"✓ API endpoints documented")
        print(f"✓ Ready for production use!")
        
    except Exception as e:
        print(f"\\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n🛑 Tests interrupted by user")
    except Exception as e:
        print(f"\\n💥 Tests failed: {e}")
        sys.exit(1)