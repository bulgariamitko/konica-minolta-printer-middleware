#!/usr/bin/env python3
"""
Test script to verify connectivity and functionality with your actual KM machines.
This will test each machine individually and then test the full middleware.
"""

import asyncio
import aiohttp
import logging
from src.konika_middleware.models.config import Settings
from src.konika_middleware.core.device_manager import DeviceManager
from src.konika_middleware.core.discovery import NetworkDiscovery
from src.konika_middleware.devices.snmp_client import SNMPClient


async def test_basic_connectivity():
    """Test basic HTTP connectivity to each machine."""
    print("🔌 TESTING BASIC CONNECTIVITY")
    print("=" * 50)
    
    machines = [
        ("192.168.1.200", "C654e"),
        ("192.168.1.210", "C759"),
        ("192.168.1.220", "C754e"),
        ("192.168.1.131", "KM2100")
    ]
    
    results = {}
    timeout = aiohttp.ClientTimeout(total=5)
    
    for ip, model in machines:
        print(f"Testing {model} at {ip}...")
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Test basic HTTP connectivity
                async with session.get(f"http://{ip}") as response:
                    http_status = response.status
                    print(f"  ✅ HTTP: {http_status}")
                    results[ip] = {"http": http_status, "accessible": True}
                    
        except Exception as e:
            print(f"  ❌ HTTP: Failed - {e}")
            results[ip] = {"http": "failed", "accessible": False, "error": str(e)}
    
    print()
    return results


async def test_snmp_discovery():
    """Test SNMP discovery on your actual machines."""
    print("📡 TESTING SNMP DISCOVERY")
    print("=" * 50)
    
    settings = Settings()
    discovery = NetworkDiscovery(settings.snmp_community)
    
    # Test specific IPs from your config
    machines = ["192.168.1.200", "192.168.1.210", "192.168.1.220", "192.168.1.131"]
    
    print("Scanning your specific machines via SNMP...")
    discovered = await discovery.quick_scan(machines)
    
    print(f"Found {len(discovered)} KM devices:")
    for device_info in discovered:
        print(f"  📱 {device_info['ip_address']}")
        print(f"     Model: {device_info.get('model', 'Unknown')}")
        print(f"     SNMP: {device_info.get('snmp_info', {}).get('description', 'No description')}")
        print(f"     HTTP: {'✅' if device_info.get('http_accessible') else '❌'}")
        print(f"     Admin Password: {'✅' if device_info.get('admin_password') else '❌'}")
        print()
    
    return discovered


async def test_device_manager():
    """Test the full device manager with your configuration."""
    print("🔧 TESTING DEVICE MANAGER")
    print("=" * 50)
    
    # Load your settings
    settings = Settings()
    print(f"Using configuration:")
    print(f"  AUTO_DISCOVER: {settings.auto_discover}")
    print(f"  MACHINE_LIST: {settings.machine_list}")
    print()
    
    # Initialize device manager
    device_manager = DeviceManager(settings)
    
    # Test device discovery
    print("Starting device discovery...")
    devices = await device_manager.discover_devices()
    
    print(f"Device manager found {len(devices)} devices:")
    for device in devices:
        print(f"  🖨️  {device.name} ({device.id})")
        print(f"      IP: {device.ip_address}")
        print(f"      Type: {device.type}")
        print(f"      Password: {'✅' if device.admin_password else '❌'}")
        print()
    
    # Test device status refresh
    if devices:
        print("Testing device status refresh...")
        await device_manager.refresh_all_devices()
        
        print("Device statuses:")
        for device in devices:
            print(f"  {device.name}: {device.status}")
    
    return devices


async def test_individual_device_connections():
    """Test individual device connections and authentication."""
    print("🔐 TESTING INDIVIDUAL DEVICE AUTHENTICATION")
    print("=" * 50)
    
    settings = Settings()
    machines = settings.parse_machine_list()
    
    for ip, password in machines:
        print(f"Testing authentication for {ip}...")
        
        try:
            # Test admin login
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
                'password': password or ''
            }
            
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(cookies=base_cookies, timeout=timeout) as session:
                url = f"http://{ip}/wcd/login.cgi"
                async with session.post(url, data=login_data) as response:
                    if response.status in [200, 302]:
                        # Check for admin cookies
                        cookies = dict(session.cookie_jar)
                        has_admin_session = any('ID' in str(cookie) for cookie in cookies)
                        
                        if has_admin_session or response.status == 302:
                            print(f"  ✅ Authentication successful")
                        else:
                            print(f"  ⚠️  HTTP {response.status} but no admin session detected")
                    else:
                        print(f"  ❌ Authentication failed: HTTP {response.status}")
                        
        except Exception as e:
            print(f"  ❌ Connection failed: {e}")
        
        print()


async def test_middleware_startup():
    """Test if the middleware can start successfully."""
    print("🚀 TESTING MIDDLEWARE STARTUP")
    print("=" * 50)
    
    try:
        # Import and test configuration loading
        from src.konika_middleware.models.config import Config
        config = Config.load()
        print("✅ Configuration loaded successfully")
        
        # Test device manager initialization
        device_manager = DeviceManager(config.settings)
        print("✅ Device manager created successfully")
        
        # Test device discovery
        devices = await device_manager.discover_devices()
        print(f"✅ Device discovery completed: {len(devices)} devices found")
        
        # Test device status refresh
        if devices:
            await device_manager.refresh_all_devices()
            print("✅ Device status refresh completed")
        
        print()
        print("🎉 MIDDLEWARE IS READY TO START!")
        print("   All components tested successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Middleware startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all connectivity and functionality tests."""
    print("🖨️  KONICA MINOLTA MIDDLEWARE - REAL MACHINE TESTING")
    print("=" * 70)
    print("Testing connectivity and functionality with your actual machines:")
    print("  • C654e (192.168.1.200)")
    print("  • C759  (192.168.1.210)")
    print("  • C754e (192.168.1.220)")
    print("  • KM2100 (192.168.1.131)")
    print()
    
    try:
        # Test 1: Basic connectivity
        connectivity_results = await test_basic_connectivity()
        
        # Test 2: SNMP discovery
        discovered_devices = await test_snmp_discovery()
        
        # Test 3: Device authentication
        await test_individual_device_connections()
        
        # Test 4: Device manager
        managed_devices = await test_device_manager()
        
        # Test 5: Middleware startup
        startup_success = await test_middleware_startup()
        
        # Summary
        print("📊 TEST SUMMARY")
        print("=" * 30)
        
        accessible_count = sum(1 for result in connectivity_results.values() if result.get('accessible'))
        print(f"Basic Connectivity: {accessible_count}/4 machines accessible")
        print(f"SNMP Discovery: {len(discovered_devices)} devices found")
        print(f"Device Manager: {len(managed_devices)} devices managed")
        print(f"Middleware Startup: {'✅ Success' if startup_success else '❌ Failed'}")
        
        if accessible_count == 4 and len(discovered_devices) > 0 and startup_success:
            print()
            print("🎉 ALL TESTS PASSED!")
            print("Your middleware is ready to manage your Konica Minolta printers!")
            print()
            print("🚀 START COMMANDS:")
            print("   python -m uvicorn src.konika_middleware.api.main:app --host 0.0.0.0 --port 8000")
            print("   OR")
            print("   ./start_middleware.sh start")
        else:
            print()
            print("⚠️  SOME TESTS FAILED")
            print("Check the error messages above for troubleshooting guidance.")
        
    except Exception as e:
        print(f"❌ TESTING FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing
    
    # Run the tests
    asyncio.run(main())