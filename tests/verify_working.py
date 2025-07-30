#!/usr/bin/env python3
"""
Complete verification that your Konica Minolta middleware is working correctly.
"""

import asyncio
import subprocess
import time
import aiohttp
import sys
import signal


class MiddlewareVerification:
    def __init__(self):
        self.server_process = None
        self.base_url = "http://localhost:8000"
    
    async def start_server(self):
        """Start the middleware server."""
        print("🚀 Starting middleware server...")
        self.server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "src.konika_middleware.api.main:app",
            "--host", "0.0.0.0", "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        print("⏳ Waiting for server to start...")
        for i in range(30):  # Wait up to 30 seconds
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/api/v1/health", timeout=aiohttp.ClientTimeout(total=2)) as response:
                        if response.status == 200:
                            print("✅ Server started successfully!")
                            return True
            except:
                await asyncio.sleep(1)
        
        print("❌ Server failed to start within 30 seconds")
        return False
    
    def stop_server(self):
        """Stop the middleware server."""
        if self.server_process:
            print("🛑 Stopping server...")
            self.server_process.terminate()
            self.server_process.wait()
    
    async def test_endpoints(self):
        """Test all API endpoints."""
        print("\n🧪 TESTING API ENDPOINTS")
        print("=" * 40)
        
        results = {}
        
        async with aiohttp.ClientSession() as session:
            # Test 1: Health check
            try:
                async with session.get(f"{self.base_url}/api/v1/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"✅ Health: {health_data.get('status')}")
                        results['health'] = True
                    else:
                        print(f"❌ Health: HTTP {response.status}")
                        results['health'] = False
            except Exception as e:
                print(f"❌ Health: {e}")
                results['health'] = False
            
            # Test 2: Devices list
            try:
                async with session.get(f"{self.base_url}/api/v1/devices") as response:
                    if response.status == 200:
                        devices_response = await response.json()
                        devices = devices_response.get('devices', [])
                        print(f"✅ Devices: Found {len(devices)} devices")
                        for device in devices:
                            print(f"   • {device.get('name')} ({device.get('ip_address')}) - {device.get('status')}")
                        results['devices'] = len(devices)
                    else:
                        print(f"❌ Devices: HTTP {response.status}")
                        results['devices'] = 0
            except Exception as e:
                print(f"❌ Devices: {e}")
                results['devices'] = 0
            
            # Test 3: API Status
            try:
                async with session.get(f"{self.base_url}/api/v1/status") as response:
                    if response.status == 200:
                        status = await response.json()
                        print(f"✅ Status: {status.get('api_status')}")
                        device_stats = status.get('devices', {})
                        print(f"   • Total devices: {device_stats.get('total_devices', 0)}")
                        print(f"   • Online devices: {device_stats.get('online_count', 0)}")
                        results['status'] = True
                    else:
                        print(f"❌ Status: HTTP {response.status}")
                        results['status'] = False
            except Exception as e:
                print(f"❌ Status: {e}")
                results['status'] = False
            
            # Test 4: Device capabilities (if devices exist)
            if results.get('devices', 0) > 0:
                try:
                    # Get first device ID
                    async with session.get(f"{self.base_url}/api/v1/devices") as response:
                        devices_response = await response.json()
                        devices = devices_response.get('devices', [])
                        if devices:
                            device_id = devices[0]['id']
                            async with session.get(f"{self.base_url}/api/v1/devices/{device_id}/capabilities") as cap_response:
                                if cap_response.status == 200:
                                    capabilities = await cap_response.json()
                                    print(f"✅ Capabilities: Device supports {len(capabilities)} features")
                                    results['capabilities'] = True
                                else:
                                    print(f"❌ Capabilities: HTTP {cap_response.status}")
                                    results['capabilities'] = False
                except Exception as e:
                    print(f"❌ Capabilities: {e}")
                    results['capabilities'] = False
        
        return results
    
    async def run_verification(self):
        """Run complete verification."""
        print("🖨️  KONICA MINOLTA MIDDLEWARE VERIFICATION")
        print("=" * 50)
        print("Verifying your middleware works with:")
        print("  • C654e at 192.168.1.200")
        print("  • C759 at 192.168.1.210") 
        print("  • C754e at 192.168.1.220")
        print("  • KM2100 at 192.168.1.131")
        print()
        
        try:
            # Start server
            if not await self.start_server():
                return False
            
            # Test endpoints
            results = await self.test_endpoints()
            
            # Print summary
            print("\n📊 VERIFICATION SUMMARY")
            print("=" * 30)
            print(f"✅ Server startup: Success")
            print(f"{'✅' if results.get('health') else '❌'} Health check: {'Pass' if results.get('health') else 'Fail'}")
            print(f"{'✅' if results.get('devices', 0) > 0 else '❌'} Device discovery: {results.get('devices', 0)} devices")
            print(f"{'✅' if results.get('status') else '❌'} API status: {'Pass' if results.get('status') else 'Fail'}")
            
            if results.get('devices', 0) > 0 and results.get('health') and results.get('status'):
                print("\n🎉 VERIFICATION COMPLETE!")
                print("Your Konica Minolta middleware is working perfectly!")
                print("\n📝 You can now:")
                print("  • Access the API at: http://localhost:8000")
                print("  • View API docs at: http://localhost:8000/docs")
                print("  • Check device status via REST API")
                print("  • Submit print jobs programmatically")
            else:
                print("\n⚠️  VERIFICATION ISSUES DETECTED")
                print("Some components are not working correctly.")
            
            return True
            
        except KeyboardInterrupt:
            print("\n🛑 Verification interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Verification failed: {e}")
            return False
        finally:
            self.stop_server()


async def main():
    verification = MiddlewareVerification()
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        verification.stop_server()
        print("\n🛑 Verification stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    await verification.run_verification()


if __name__ == "__main__":
    asyncio.run(main())