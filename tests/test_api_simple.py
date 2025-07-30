#!/usr/bin/env python3
"""
Simple API test to verify the middleware works with your machines.
"""

import asyncio
import aiohttp
import json


async def test_api():
    """Test the middleware API endpoints."""
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("🏥 Testing health endpoint...")
        async with session.get(f"{base_url}/api/v1/health") as response:
            if response.status == 200:
                health_data = await response.json()
                print(f"✅ Health: {health_data.get('status', 'unknown')}")
            else:
                print(f"❌ Health check failed: {response.status}")
        
        # Test devices endpoint
        print("\n🖨️  Testing devices endpoint...")
        async with session.get(f"{base_url}/api/v1/devices") as response:
            if response.status == 200:
                devices_data = await response.json()
                print(f"✅ Found {len(devices_data)} devices:")
                for device in devices_data:
                    print(f"   - {device.get('name')} at {device.get('ip_address')} ({device.get('status')})")
            else:
                print(f"❌ Devices endpoint failed: {response.status}")
        
        # Test API status
        print("\n📊 Testing API status...")
        async with session.get(f"{base_url}/api/v1/status") as response:
            if response.status == 200:
                status_data = await response.json()
                print(f"✅ API Status: {status_data.get('api_status')}")
                print(f"   Devices: {status_data.get('devices', {})}")
            else:
                print(f"❌ Status endpoint failed: {response.status}")


if __name__ == "__main__":
    print("🧪 TESTING MIDDLEWARE API")
    print("=" * 40)
    print("Make sure the middleware is running first:")
    print("  python -m uvicorn src.konika_middleware.api.main:app --host 0.0.0.0 --port 8000")
    print()
    
    asyncio.run(test_api())