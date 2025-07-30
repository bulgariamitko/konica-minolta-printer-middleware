#!/usr/bin/env python3
"""
Deep investigation of C759 and C754e that aren't being detected.
This will test various connection methods and protocols.
"""

import asyncio
import aiohttp
import socket
import subprocess
from typing import Dict, Any, List


async def basic_connectivity_test(ip: str, model: str) -> Dict[str, Any]:
    """Test basic network connectivity."""
    print(f"\n🔌 BASIC CONNECTIVITY TEST - {model} ({ip})")
    print("-" * 50)
    
    results = {}
    
    # Ping test
    try:
        result = subprocess.run(['ping', '-c', '3', ip], 
                              capture_output=True, text=True, timeout=10)
        ping_success = result.returncode == 0
        print(f"Ping: {'✅ Success' if ping_success else '❌ Failed'}")
        results['ping'] = ping_success
        if ping_success:
            # Extract ping times
            lines = result.stdout.split('\n')
            for line in lines:
                if 'time=' in line:
                    print(f"  {line.strip()}")
    except Exception as e:
        print(f"Ping: ❌ Error - {e}")
        results['ping'] = False
    
    # Port scanning
    common_ports = [80, 443, 8080, 8443, 9100, 631, 515, 161, 162, 21, 22, 23]
    open_ports = []
    
    print(f"\nPort Scanning:")
    for port in common_ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            result = sock.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
                print(f"  Port {port}: ✅ Open")
            sock.close()
        except Exception:
            pass
    
    results['open_ports'] = open_ports
    print(f"Open ports: {open_ports}")
    
    return results


async def http_deep_scan(ip: str, model: str) -> Dict[str, Any]:
    """Deep HTTP scanning with various paths and methods."""
    print(f"\n🌐 HTTP DEEP SCAN - {model} ({ip})")
    print("-" * 50)
    
    results = {}
    timeout = aiohttp.ClientTimeout(total=10)
    
    # Test various HTTP paths that printers commonly use
    test_paths = [
        '/',
        '/wcd/',
        '/wcd/index.html',
        '/status',
        '/info',
        '/login',
        '/admin',
        '/printer',
        '/fiery/',
        '/api/',
        '/web/',
        '/system/',
        '/device/',
        '/jobs/',
        '/queue/',
        '/capabilities',
        '/deviceinfo',
        '/command/',
        '/wsi/',
        '/cws/',  # Command WorkStation
        '/print/',
        '/config/',
        '/maintenance/',
        '/utilities/',
    ]
    
    accessible_paths = []
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for path in test_paths:
                try:
                    url = f"http://{ip}{path}"
                    async with session.get(url) as response:
                        if response.status in [200, 301, 302, 401, 403]:
                            accessible_paths.append({
                                'path': path,
                                'status': response.status,
                                'content_type': response.headers.get('content-type', 'unknown'),
                                'server': response.headers.get('server', 'unknown')
                            })
                            print(f"  {path}: {response.status} - {response.headers.get('content-type', 'unknown')}")
                            
                            # Get a sample of content for analysis
                            if response.status == 200:
                                content = await response.text()
                                content_sample = content[:200].replace('\n', ' ').replace('\r', '')
                                print(f"    Content: {content_sample}...")
                                
                except Exception as e:
                    # Silently continue - too many paths to show all errors
                    pass
    
    except Exception as e:
        print(f"HTTP scan error: {e}")
    
    results['accessible_paths'] = accessible_paths
    print(f"\nFound {len(accessible_paths)} accessible HTTP paths")
    
    return results


async def snmp_detailed_test(ip: str, model: str) -> Dict[str, Any]:
    """Detailed SNMP testing with different communities and versions."""
    print(f"\n📡 SNMP DETAILED TEST - {model} ({ip})")
    print("-" * 50)
    
    results = {}
    
    # Test different SNMP communities
    communities = ['public', 'private', 'admin', 'printer', '', 'konica', 'minolta']
    
    for community in communities:
        try:
            from src.konika_middleware.devices.snmp_client import SNMPClient
            snmp_client = SNMPClient(ip, community)
            device_info = await snmp_client.get_device_info()
            
            if device_info:
                print(f"✅ SNMP Success with community: '{community}'")
                print(f"   Description: {device_info.get('description', 'Unknown')}")
                print(f"   Contact: {device_info.get('contact', 'Unknown')}")
                print(f"   Location: {device_info.get('location', 'Unknown')}")
                results[f'snmp_{community}'] = device_info
                break
            else:
                print(f"❌ SNMP Failed with community: '{community}'")
                
        except Exception as e:
            print(f"❌ SNMP Error with community '{community}': {e}")
    
    return results


async def printer_protocol_test(ip: str, model: str) -> Dict[str, Any]:
    """Test various printer protocols."""
    print(f"\n🖨️  PRINTER PROTOCOL TEST - {model} ({ip})")
    print("-" * 50)
    
    results = {}
    
    # Test IPP (Internet Printing Protocol)
    try:
        ipp_urls = [
            f"http://{ip}:631/",
            f"http://{ip}:631/ipp/",
            f"http://{ip}:631/printers/",
            f"http://{ip}/ipp/",
        ]
        
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for ipp_url in ipp_urls:
                try:
                    async with session.get(ipp_url) as response:
                        if response.status in [200, 401]:
                            print(f"✅ IPP accessible: {ipp_url} ({response.status})")
                            results['ipp_accessible'] = True
                            break
                except Exception:
                    continue
    except Exception as e:
        print(f"IPP test error: {e}")
    
    # Test raw printing port
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, 9100))
        if result == 0:
            print(f"✅ Raw printing port (9100) is open")
            results['raw_print_port'] = True
        else:
            print(f"❌ Raw printing port (9100) is closed")
            results['raw_print_port'] = False
        sock.close()
    except Exception as e:
        print(f"Raw port test error: {e}")
    
    return results


async def investigate_machine(ip: str, model: str):
    """Complete investigation of a single machine."""
    print(f"\n🔍 INVESTIGATING {model} AT {ip}")
    print("=" * 60)
    
    # Run all tests
    connectivity = await basic_connectivity_test(ip, model)
    http_results = await http_deep_scan(ip, model)
    snmp_results = await snmp_detailed_test(ip, model)
    printer_results = await printer_protocol_test(ip, model)
    
    # Summary
    print(f"\n📊 INVESTIGATION SUMMARY - {model}")
    print("-" * 40)
    print(f"Ping: {'✅' if connectivity.get('ping') else '❌'}")
    print(f"Open Ports: {connectivity.get('open_ports', [])}")
    print(f"HTTP Paths: {len(http_results.get('accessible_paths', []))}")
    print(f"SNMP: {'✅' if any('snmp_' in k for k in snmp_results.keys()) else '❌'}")
    print(f"IPP: {'✅' if printer_results.get('ipp_accessible') else '❌'}")
    print(f"Raw Print: {'✅' if printer_results.get('raw_print_port') else '❌'}")
    
    return {
        'connectivity': connectivity,
        'http': http_results,
        'snmp': snmp_results,
        'printer': printer_results
    }


async def main():
    """Investigate the missing C759 and C754e machines."""
    print("🕵️  INVESTIGATING MISSING KONICA MINOLTA MACHINES")
    print("=" * 70)
    print("Deep investigation of machines not detected by standard methods:")
    print("  • C759 (192.168.1.210) - Should have Fiery controller")
    print("  • C754e (192.168.1.220) - Should have Fiery controller")
    print()
    
    missing_machines = [
        ("192.168.1.210", "C759"),
        ("192.168.1.220", "C754e")
    ]
    
    all_results = {}
    
    for ip, model in missing_machines:
        try:
            results = await investigate_machine(ip, model)
            all_results[model] = results
        except Exception as e:
            print(f"❌ Investigation failed for {model}: {e}")
    
    # Final analysis
    print(f"\n\n🧪 FINAL ANALYSIS")
    print("=" * 30)
    
    for model, results in all_results.items():
        print(f"\n{model}:")
        if results['connectivity']['ping']:
            print("  ✅ Machine is reachable")
            if results['http']['accessible_paths']:
                print("  ✅ Has web interface")
                print(f"     Most likely interface: {results['http']['accessible_paths'][0]['path']}")
            if any('snmp_' in k for k in results['snmp'].keys()):
                print("  ✅ SNMP is working (discovery should find this)")
            else:
                print("  ❌ SNMP not working (explains why not found)")
            
            if results['printer']['ipp_accessible']:
                print("  ✅ IPP printing available")
            if results['printer']['raw_print_port']:
                print("  ✅ Raw printing available")
        else:
            print("  ❌ Machine is not reachable - check IP address or network")
    
    print("\n📝 RECOMMENDATIONS:")
    print("1. If machines are reachable but SNMP fails:")
    print("   - Check SNMP settings on the printers")
    print("   - Try different SNMP communities")
    print("   - Enable SNMP in printer network settings")
    print("2. If machines have web interfaces:")
    print("   - We can add manual device entries")
    print("   - Use HTTP-based detection instead of SNMP")
    print("3. If Fiery controllers are present:")
    print("   - Look for /command/ or /fiery/ paths")
    print("   - Check for Fiery-specific endpoints")


if __name__ == "__main__":
    asyncio.run(main())